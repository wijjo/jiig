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
from typing import List, Text

# This module works with all the major sub-packages, and simple names like
# "driver" and "runtime" are useful for local variables. So use full package
# names to avoid naming conflicts between local variables and packages.
import jiig.driver
import jiig.registry
import jiig.util

from .hints import add_supported_hints, get_bad_hints
from .runtime_task import RuntimeTask
from .runtime_tool import RuntimeTool
from .tool import Tool, TOP_TASK_LABEL, SUB_TASK_LABEL, TOP_TASK_DEST_NAME


def _check_virtual_environment(runner_args: List[Text],
                               cli_args: List[Text],
                               tool: RuntimeTool):
    # Check if virtual environment needs to be activated.
    if not tool.venv_needed:
        jiig.util.console.log_message('Virtual environment is unnecessary.', debug=True)
        return
    if tool.venv_active:
        jiig.util.console.log_message('Virtual environment is active.', debug=True)
        return

    # Restart in venv.
    jiig.util.console.log_message('Activating virtual environment...', debug=True)
    jiig.util.python.build_virtual_environment(tool.venv_folder,
                                               packages=tool.pip_packages,
                                               rebuild=False,
                                               quiet=True)
    # Restart inside the virtual environment with '--' inserted to help parsing.
    args = [tool.venv_interpreter]
    if runner_args is not None:
        args.extend(runner_args)
    args.append('--')
    args.extend(cli_args)
    # Remember the original parent Python executable in an environment variable
    # in case the virtual environment needs to be rebuilt.
    os.environ[jiig.util.python.PYTHON_NATIVE_ENVIRONMENT_NAME] = sys.executable
    os.execv(args[0], args)
    # Does not return from here.


class ArgumentNameError(RuntimeError):
    pass


class _ArgumentDataPreparer:

    def __init__(self, raw_data: object):
        self.raw_data = raw_data
        self.prepared_data = {}
        self.errors: List[Text] = []

    def prepare_argument_data(self, task: RuntimeTask):
        # Convert raw argument data to prepared data.
        # Handle lower and upper case attribute names in raw data.
        for name, field in task.fields.items():
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
                        value = field.default.value if field.default is not None else None
                    self.prepared_data[name] = value
                except (TypeError, ValueError) as exc:
                    self.errors.append(
                        jiig.util.general.format_exception(exc,
                                                           label=f'{name}:{adapter_name}',
                                                           skip_stack_levels=1))


def _execute(runtime: jiig.contexts.Runtime, task_stack: List[RuntimeTask], data: object):
    # Prepare argument data using raw data and task option/argument definitions.
    data_preparer = _ArgumentDataPreparer(data)
    for task in task_stack:
        data_preparer.prepare_argument_data(task)
    if len(data_preparer.errors) > 0:
        plural_failure = jiig.util.general.plural("failure", data_preparer.errors)
        jiig.util.console.abort(f'{len(data_preparer.errors)} argument {plural_failure}:',
                                *data_preparer.errors)
    try:
        # Invoke task stack @run call-backs in top to bottom order.
        handlers: List[RuntimeTask] = []
        for task in task_stack:
            # Extract the data needed to populate task dataclass fields.
            # noinspection PyDataclass
            task_field_data = {field.name: data_preparer.prepared_data[field.name]
                               for field in dataclasses.fields(task.handler_class)
                               if field.name in data_preparer.prepared_data}
            try:
                # Instantiate the task handler class with required field data. Non-field
                # data members and type mismatches may cause errors.
                handler_instance = task.handler_class(**task_field_data)
                handlers.append(handler_instance)
                run_method = getattr(handler_instance, 'on_run', None)
                if ismethod(run_method):
                    try:
                        run_method(runtime)
                    except Exception as exc:
                        jiig.util.console.abort(f'Exception invoking::'
                                                f' {handler_instance.__class__.__module__}'
                                                f'.{handler_instance.__class__.__name__}.on_run()',
                                                exc,
                                                exception_traceback_skip=1)
            except Exception as exc:
                jiig.util.console.abort(f'Exception constructing:'
                                        f' {task.handler_class.__module__}'
                                        f'.{task.handler_class.__name__}',
                                        exc,
                                        exception_traceback_skip=1)
        # Invoke task stack @done call-backs in reverse order.
        while handlers:
            handler_instance = handlers.pop()
            done_method = getattr(handler_instance, 'on_done', None)
            if ismethod(done_method):
                done_method(runtime)
    except KeyboardInterrupt:
        sys.stdout.write(os.linesep)
    except ArgumentNameError as exc:
        jiig.util.console.abort(str(exc))
    except Exception as exc:
        active_names = [sub_task.name for sub_task in task_stack]
        jiig.util.console.abort(f'Task command failed:',
                                ' '.join(active_names),
                                exc,
                                exception_traceback_skip=1)


def _populate_driver_task(driver_task: jiig.driver.DriverTask, task: RuntimeTask):
    for name, field in task.fields.items():
        driver_task.add_field(name=name,
                              description=field.description,
                              element_type=field.element_type,
                              hints=field.hints,
                              default=field.default,
                              repeat=field.repeat,
                              choices=field.choices)
    for name, sub_task in task.sub_tasks.items():
        driver_sub_task = driver_task.add_sub_task(name,
                                                   sub_task.description,
                                                   sub_task.notes,
                                                   sub_task.footnotes,
                                                   sub_task.visibility)
        _populate_driver_task(driver_sub_task, sub_task)


def _add_builtin_tasks(tool: RuntimeTool):
    visibility = 2 if tool.options.hide_builtin_tasks else 1

    def _add_if_needed(name: Text, task_ref: Text):
        if f'{name}[s]' in tool.root_task.sub_tasks:
            return
        if f'{name}[h]' in tool.root_task.sub_tasks:
            return
        task = RuntimeTask.resolve(task_ref, name, visibility)
        if task is not None:
            tool.root_task.sub_tasks[name] = task

    if not tool.options.disable_help:
        _add_if_needed('help', 'jiig.tasks.help')
    if not tool.options.disable_alias:
        _add_if_needed('alias', 'jiig.tasks.alias')
    if tool.venv_needed:
        _add_if_needed('venv', 'jiig.tasks.venv')


def main(registered_tool: Tool,
         runner_args: List[Text] = None,
         cli_args: List[Text] = None,
         ):
    """
    Main function called from jiig-run to drive tool and task initialization.

    :param registered_tool: registered tool configuration object
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
    tool = RuntimeTool(registered_tool)

    # Construct the driver.
    supported_global_options: List[Text] = []
    if not registered_tool.tool_options.disable_debug:
        supported_global_options.append('debug')
    if not registered_tool.tool_options.disable_dry_run:
        supported_global_options.append('dry_run')
    if not registered_tool.tool_options.disable_verbose:
        supported_global_options.append('verbose')
    if registered_tool.tool_options.enable_pause:
        supported_global_options.append('pause')
    if registered_tool.tool_options.enable_keep_files:
        supported_global_options.append('keep_files')
    driver_options = jiig.driver.DriverOptions(
        variant=registered_tool.driver_variant,
        raise_exceptions=True,
        top_task_label=TOP_TASK_LABEL,
        sub_task_label=SUB_TASK_LABEL,
        top_task_dest_name=TOP_TASK_DEST_NAME,
        supported_global_options=supported_global_options,
    )
    driver_registration = jiig.registry.DRIVER_REGISTRY.resolve(registered_tool.driver)
    driver = driver_registration.registered_class(registered_tool.tool_name,
                                                  registered_tool.description,
                                                  options=driver_options)

    # Initialize the driver. Only display message once.
    driver_initialization_data = driver.initialize_driver(raw_arguments)
    if not tool.venv_active:
        jiig.util.console.log_message('Jiig driver initialized.', debug=True)

    # Push initialized options from the driver into libraries.
    jiig.options.Options.debug = 'debug' in driver.enabled_global_options
    jiig.options.Options.dry_run = 'dry_run' in driver.enabled_global_options
    jiig.options.Options.verbose = 'verbose' in driver.enabled_global_options
    jiig.options.Options.pause = 'pause' in driver.enabled_global_options
    jiig.options.Options.keep_files = 'keep_files' in driver.enabled_global_options
    jiig.util.options.Options.debug = jiig.options.Options.debug
    jiig.util.options.Options.dry_run = jiig.options.Options.dry_run
    jiig.util.options.Options.verbose = jiig.options.Options.verbose
    jiig.util.options.Options.pause = jiig.options.Options.pause
    jiig.util.options.Options.keep_files = jiig.options.Options.keep_files

    # Check if a virtual environment is required, but not active. If so, it
    # restarts inside the virtual environment (and does not return from call).
    _check_virtual_environment(runner_args, cli_args, tool)

    # Initialize the Python library load path.
    for lib_folder in reversed(tool.library_folders):
        if os.path.isdir(lib_folder) and lib_folder not in sys.path:
            sys.path.insert(0, lib_folder)

    # Resolve a custom runtime context class.
    if registered_tool.runtime is not None:
        registered_runtime = jiig.registry.CONTEXT_REGISTRY.resolve(registered_tool.runtime,
                                                                    required=True)
        runtime_class = registered_runtime.registered_class
    else:
        runtime_class = jiig.contexts.Runtime

    # Resolve the root task.
    if not tool.root_task.sub_tasks:
        jiig.util.console.abort('There are no registered tasks.')

    # Add automatic built-in secondary or hidden sub-tasks, if not disabled.
    _add_builtin_tasks(tool)

    # Convert the runtime task hierarchy to a driver task hierarchy.
    # Add automatic secondary ('...[s]') sub-tasks, if not disabled.
    driver_root_task: jiig.driver.DriverTask = jiig.driver.DriverTask(
        registered_tool.tool_name, '', [], [], [], {}, 0)
    _populate_driver_task(driver_root_task, tool.root_task)

    # Just display help if there are no arguments to process.
    if not driver_initialization_data.final_arguments:
        driver.provide_help(driver_root_task)
        sys.exit(0)

    driver_app_data = driver.initialize_application(driver_initialization_data,
                                                    driver_root_task)
    jiig.util.console.log_message('Application initialized.', debug=True)

    # Check hint usage.
    add_supported_hints('repeat', 'choices', 'default')
    if driver.supported_hints:
        add_supported_hints(*driver.supported_hints)
    bad_hints = get_bad_hints()
    if bad_hints:
        plural_hint = jiig.util.general.plural("hint", bad_hints)
        jiig.util.console.log_error(f'Bad field {plural_hint}:', *bad_hints)

    # Convert driver task stack to RegisteredTask stack.
    task_stack: List[RuntimeTask] = [tool.root_task]
    for driver_task in driver_app_data.task_stack:
        task_stack.append(task_stack[-1].sub_tasks[driver_task.name])

    class HelpGenerator(jiig.contexts.RuntimeHelpGenerator):
        def generate_help(self, *names: Text, show_hidden: bool = False):
            driver.provide_help(driver_root_task, *names, show_hidden=show_hidden)

    # Create and initialize root Runtime context.
    runtime = runtime_class(None,
                            tool=tool,
                            help_generator=HelpGenerator(),
                            data=driver_app_data.data)

    jiig.util.console.log_message('Executing application...', debug=True)
    _execute(runtime, task_stack, driver_app_data.data)


def tool_script_main():
    """Called by program run by "shebang" line of tool script."""
    main(Tool.from_script(sys.argv[1]),
         runner_args=sys.argv[:2],
         cli_args=sys.argv[2:])
