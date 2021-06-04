"""
Jiig main function to boot the tool.

Consists of a series of function calls into the initialization package.

The `initializers` package modules each provide an `initialize()` function. The
`initialize()` function receives previously-loaded data, which it massages, as
needed, and applies to tool state, as appropriate.

Note that by convention `initializers` modules are either read-only or
write-only. Read-only modules are kept side-effect-free and return loaded data.
Write-only modules return no data.
"""

import os
import sys
import dataclasses
from inspect import ismethod
from typing import List, Text, Type, Dict

from . import driver, registry, runtime, util

from .util.console import log_message, log_error, abort
from .util.general import format_exception, plural
from .util.python import build_virtual_environment, PYTHON_NATIVE_ENVIRONMENT_NAME


def _check_virtual_environment(runner_args: List[Text],
                               cli_args: List[Text],
                               runtime_tool: runtime.RuntimeTool):
    # Check if virtual environment needs to be activated.
    if not runtime_tool.venv_needed:
        log_message('Virtual environment is unnecessary.', debug=True)
        return
    if runtime_tool.venv_active:
        log_message('Virtual environment is active.', debug=True)
        return

    # Restart in venv.
    log_message('Activating virtual environment...', debug=True)
    build_virtual_environment(runtime_tool.venv_folder,
                              packages=runtime_tool.pip_packages,
                              rebuild=False,
                              quiet=True)
    # Restart inside the virtual environment with '--' inserted to help parsing.
    args = [runtime_tool.venv_interpreter]
    if runner_args is not None:
        args.extend(runner_args)
    args.append('--')
    args.extend(cli_args)
    # Remember the original parent Python executable in an environment variable
    # in case the virtual environment needs to be rebuilt.
    os.environ[PYTHON_NATIVE_ENVIRONMENT_NAME] = sys.executable
    os.execv(args[0], args)
    # Does not return from here.


class ArgumentNameError(RuntimeError):
    pass


class _ArgumentDataPreparer:

    def __init__(self, raw_data: object):
        self.raw_data = raw_data
        self.prepared_data = {}
        self.errors: List[Text] = []

    def prepare_argument_data(self, task_runtime: runtime.RuntimeTask):
        # Convert raw argument data to prepared data.
        # Handle lower and upper case attribute names in raw data.
        for name, field in task_runtime.fields.items():
            value = None
            has_attribute = hasattr(self.raw_data, name)
            if has_attribute:
                value = getattr(self.raw_data, name)
            else:
                dest_name = name.upper()
                has_attribute = hasattr(self.raw_data, dest_name)
                if has_attribute:
                    value = getattr(self.raw_data, dest_name)
            if has_attribute:
                adapter_name = '???'
                try:
                    # Call all adapters to validate and convert as appropriate.
                    if value is not None:
                        if field.adapters is not None:
                            for adapter in field.adapters:
                                adapter_name = adapter.__name__
                                if field.repeat is not None:
                                    value = [adapter(value_item) for value_item in value]
                                else:
                                    value = adapter(value)
                    else:
                        value = field.default
                    self.prepared_data[name] = value
                except (TypeError, ValueError) as exc:
                    self.errors.append(
                        format_exception(exc,
                                         label=f'{name}:{adapter_name}',
                                         skip_stack_levels=1))


def _invoke_task_handler(runtime_task: runtime.RuntimeTask,
                         data_dict: Dict,
                         ) -> runtime.Task:
    # Extract the data needed to populate task dataclass fields.
    # noinspection PyDataclass
    task_field_data = {field.name: data_dict[field.name]
                       for field in dataclasses.fields(runtime_task.handler_class)
                       if field.name in data_dict}
    try:
        return runtime_task.handler_class(**task_field_data)
    except Exception as exc:
        abort(f'Unable to construct task handler class:'
              f' {runtime_task.handler_class.__module__}'
              f'.{runtime_task.handler_class.__name__}',
              exc)


def _execute(runtime_obj: runtime.Runtime,
             active_task_stack: List[runtime.RuntimeTask],
             data: object,
             ):
    # Prepare argument data using raw data and task option/argument definitions.
    data_preparer = _ArgumentDataPreparer(data)
    for task_runtime in active_task_stack:
        data_preparer.prepare_argument_data(task_runtime)
    if len(data_preparer.errors) > 0:
        abort(f'{len(data_preparer.errors)} argument failure(s):', *data_preparer.errors)
    try:
        # Invoke task stack @run call-backs in top to bottom order.
        handlers: List[runtime.Task] = []
        for task_runtime in active_task_stack:
            # Instantiate the task handler class with required field data. Non-field
            # data members and type mismatches may cause errors.
            # noinspection PyBroadException
            handler = _invoke_task_handler(task_runtime, data_preparer.prepared_data)
            handlers.append(handler)
            run_method = getattr(handler, 'on_run', None)
            if ismethod(run_method):
                run_method(runtime_obj)
        # Invoke task stack @done call-backs in reverse order.
        while handlers:
            handler = handlers.pop()
            done_method = getattr(handler, 'on_done', None)
            if ismethod(done_method):
                done_method(runtime_obj)
    except KeyboardInterrupt:
        sys.stdout.write(os.linesep)
    except ArgumentNameError as exc:
        abort(str(exc))
    except Exception as exc:
        active_names = [sub_task.name for sub_task in active_task_stack]
        abort(f'Task command failed:', ' '.join(active_names), exc)


def _populate_driver_task(driver_task: driver.DriverTask,
                          runtime_task: runtime.RuntimeTask,
                          ):
    for name, field in runtime_task.fields.items():
        driver_task.add_field(name=name,
                              description=field.description,
                              element_type=field.element_type,
                              hints=field.hints,
                              default=field.default,
                              repeat=field.repeat,
                              choices=field.choices)
    for name, sub_task in runtime_task.sub_tasks.items():
        driver_sub_task = driver_task.add_sub_task(name,
                                                   sub_task.description,
                                                   sub_task.notes,
                                                   sub_task.footnotes,
                                                   sub_task.visibility)
        _populate_driver_task(driver_sub_task, sub_task)


def _add_builtin_tasks(tool_config: registry.Tool,
                       runtime_tool: runtime.RuntimeTool,
                       runtime_root_task: runtime.RuntimeTask,
                       ):
    visibility = 2 if tool_config.tool_options.hide_builtin_tasks else 1

    def _add_if_needed(name: Text, task_ref: Text):
        if f'{name}[s]' in runtime_root_task.sub_tasks:
            return
        if f'{name}[h]' in runtime_root_task.sub_tasks:
            return
        task = runtime.RuntimeTask.resolve(task_ref, name, visibility)
        runtime_root_task.sub_tasks[name] = task

    if not tool_config.tool_options.disable_help:
        _add_if_needed('help', 'jiig.tasks.help')
    if not tool_config.tool_options.disable_alias:
        _add_if_needed('alias', 'jiig.tasks.alias.root')
    if runtime_tool.venv_needed:
        _add_if_needed('venv', 'jiig.tasks.venv.root')


def main(tool_config: registry.Tool,
         jiig_driver_class: Type[driver.Driver],
         driver_variant: Text = None,
         runner_args: List[Text] = None,
         cli_args: List[Text] = None,
         ):
    """
    Main function called from jiig-run to drive tool and task initialization.

    :param tool_config: tool configuration object
    :param jiig_driver_class: pre-selected driver class to initialize and run the app
    :param driver_variant: driver implementation variant name (with default fall-back)
    :param runner_args: optional Jiig runner preamble, e.g. for jiig-run
    :param cli_args: command line arguments to override the default, sys.argv[1:]
    """
    # TODO: There is a lot of data copying to keep driver world encapsulated.
    # Consider deriving from driver data classes to avoid copying.
    # Filter out leading '--' used when restarting in virtual environment.
    if runner_args is None:
        runner_args = []
    if cli_args is None:
        cli_args = sys.argv[1:]
    if cli_args and cli_args[0] == '--':
        raw_arguments = cli_args[1:]
    else:
        raw_arguments = cli_args

    # Wrap the tool configuration so that all necessary tool data is resolved.
    runtime_tool = runtime.RuntimeTool(tool_config)

    # Construct the driver.
    supported_global_options: List[Text] = []
    if not tool_config.tool_options.disable_debug:
        supported_global_options.append('debug')
    if not tool_config.tool_options.disable_dry_run:
        supported_global_options.append('dry_run')
    if not tool_config.tool_options.disable_verbose:
        supported_global_options.append('verbose')
    if tool_config.tool_options.enable_pause:
        supported_global_options.append('pause')
    if tool_config.tool_options.enable_keep_files:
        supported_global_options.append('keep_files')
    driver_options = driver.DriverOptions(
        variant=driver_variant,
        raise_exceptions=True,
        top_task_label=registry.TOP_TASK_LABEL,
        sub_task_label=registry.SUB_TASK_LABEL,
        top_task_dest_name=registry.TOP_TASK_DEST_NAME,
        supported_global_options=supported_global_options,
    )
    jiig_driver = jiig_driver_class(tool_config.tool_name,
                                    tool_config.description,
                                    options=driver_options)

    # Initialize the driver. Only display message once.
    driver_initialization_data = jiig_driver.initialize_driver(raw_arguments)
    if not runtime_tool.venv_active:
        log_message('Jiig driver initialized.', debug=True)

    # Push initialized options from the driver into libraries.
    runtime.Options.debug = 'debug' in jiig_driver.enabled_global_options
    runtime.Options.dry_run = 'dry_run' in jiig_driver.enabled_global_options
    runtime.Options.verbose = 'verbose' in jiig_driver.enabled_global_options
    runtime.Options.pause = 'pause' in jiig_driver.enabled_global_options
    runtime.Options.keep_files = 'keep_files' in jiig_driver.enabled_global_options
    util.Options.debug = runtime.Options.debug
    util.Options.dry_run = runtime.Options.dry_run
    util.Options.verbose = runtime.Options.verbose
    util.Options.pause = runtime.Options.pause
    util.Options.keep_files = runtime.Options.keep_files

    # Check if a virtual environment is required, but not active. If so, it
    # restarts inside the virtual environment (and does not return from call).
    _check_virtual_environment(runner_args, cli_args, runtime_tool)

    # Initialize the Python library load path.
    for lib_folder in reversed(runtime_tool.library_folders):
        if os.path.isdir(lib_folder) and lib_folder not in sys.path:
            sys.path.insert(0, lib_folder)

    # Resolve the root task.
    runtime_root_task = runtime.RuntimeTask.resolve(
        runtime_tool.root_task_reference, tool_config.tool_name, 2)
    if runtime_root_task is None:
        abort('Failed to load tasks.')
    if not runtime_root_task.sub_tasks:
        abort('There are no registered tasks.')

    # Add automatic built-in secondary or hidden sub-tasks, if not disabled.
    _add_builtin_tasks(tool_config, runtime_tool, runtime_root_task)

    # Convert the runtime task hierarchy to a driver task hierarchy.
    # Add automatic secondary ('...[s]') sub-tasks, if not disabled.
    driver_root_task: driver.DriverTask = driver.DriverTask(
        tool_config.tool_name, '', [], [], [], {}, 0)
    _populate_driver_task(driver_root_task, runtime_root_task)

    # Just display help if there are no arguments to process.
    if not driver_initialization_data.final_arguments:
        jiig_driver.provide_help(driver_root_task)
        sys.exit(0)

    driver_app_data = jiig_driver.initialize_application(driver_initialization_data,
                                                         driver_root_task)
    log_message('Application initialized.', debug=True)

    # Check hint usage.
    registry.add_supported_hints('repeat', 'choices')
    if jiig_driver.supported_hints:
        registry.add_supported_hints(*jiig_driver.supported_hints)
    bad_hints = registry.get_bad_hints()
    if bad_hints:
        log_error(f'Bad field {plural("hint", bad_hints)}:', *bad_hints)

    # Convert driver task stack to RegisteredTask stack.
    task_stack: List[runtime.RuntimeTask] = [runtime_root_task]
    for driver_task in driver_app_data.task_stack:
        task_stack.append(task_stack[-1].sub_tasks[driver_task.name])

    runtime_obj = runtime.Runtime(tool=runtime_tool,
                                  root_task=runtime_root_task,
                                  driver_root_task=driver_root_task,
                                  driver=jiig_driver)

    log_message('Executing application...', debug=True)
    _execute(runtime_obj, task_stack, driver_app_data.data)


def tool_script_main():
    """Called by program run by "shebang" line of tool script."""
    main(registry.Tool.from_script(sys.argv[1]),
         driver.CLIDriver,
         runner_args=sys.argv[:2],
         cli_args=sys.argv[2:])
