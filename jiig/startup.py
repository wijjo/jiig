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
from inspect import ismethod, isfunction, isclass
from typing import List, Text, Callable, Tuple, Dict

from .driver import DriverOptions, DriverTask
from .registry import CONTEXT_REGISTRY, DRIVER_REGISTRY, HINT_REGISTRY, TASK_REGISTRY, \
    Runtime, RuntimeHelpGenerator, Tool, TaskField, AssignedTask, \
    SUB_TASK_LABEL, TOP_TASK_LABEL, TOP_TASK_DEST_NAME
from .util.general import format_exception, plural
from .util.log import abort, log_error, log_message, set_log_writer
from .util.options import OPTIONS
from .util.python import build_virtual_environment, PYTHON_NATIVE_ENVIRONMENT_NAME


def _check_virtual_environment(runner_args: List[Text],
                               cli_args: List[Text],
                               tool: Tool):
    # Check if virtual environment needs to be activated.
    if not tool.venv_needed:
        log_message('Virtual environment is unnecessary.', debug=True)
        return
    if tool.venv_active:
        log_message('Virtual environment is active.', debug=True)
        return

    # Restart in venv.
    log_message('Activating virtual environment...', debug=True)
    build_virtual_environment(tool.venv_folder,
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

    def prepare_argument_data(self, assigned_task: AssignedTask):
        # Convert raw argument data to prepared data.
        # Handle lower and upper case attribute names in raw data.
        for registered_field in assigned_task.fields:
            value = None
            has_attribute = hasattr(self.raw_data, registered_field.name)
            if has_attribute:
                value = getattr(self.raw_data, registered_field.name)
            else:
                dest_name = registered_field.name.upper()
                has_attribute = hasattr(self.raw_data, dest_name)
                if has_attribute:
                    value = getattr(self.raw_data, dest_name)
            if has_attribute:
                adapter_name = '???'
                try:
                    # Call all adapters to validate and convert as appropriate.
                    if value is not None:
                        if registered_field.adapters is not None:
                            for adapter in registered_field.adapters:
                                adapter_name = adapter.__name__
                                if registered_field.repeat is not None:
                                    value = [adapter(value_item) for value_item in value]
                                else:
                                    value = adapter(value)
                    else:
                        if registered_field.default is not None:
                            value = registered_field.default.value
                        else:
                            value = None
                    self.prepared_data[registered_field.name] = value
                except (TypeError, ValueError) as exc:
                    arg_name = registered_field.name.upper()
                    if OPTIONS.debug:
                        label = f'{assigned_task.full_name}:{arg_name}' \
                                f':adapter={adapter_name}'
                        self.errors.append(
                            format_exception(exc, label=label, skip_stack_levels=1))
                    else:
                        self.errors.append(f'{arg_name}: {str(exc)}')


def _execute(runtime: Runtime, task_stack: List[AssignedTask], data: object):
    # Prepare argument data using raw data and task option/argument definitions.
    data_preparer = _ArgumentDataPreparer(data)
    for task in task_stack:
        data_preparer.prepare_argument_data(task)
    if len(data_preparer.errors) > 0:
        abort(f'{len(data_preparer.errors)} argument'
              f' {plural("failure", data_preparer.errors)}:',
              *data_preparer.errors)
    try:
        # Run functions are invoked outer to inner, and done functions are
        # invoked in reverse order. The string is the name used for errors. The
        # dict is for keyword call arguments (task functions only).
        run_calls: List[Tuple[Text, Callable, Dict]] = []
        done_calls: List[Tuple[Text, Callable, Dict]] = []
        for task in task_stack:
            # Extract the data needed to populate task dataclass fields.
            # noinspection PyDataclass
            task_field_data = {
                field.name: data_preparer.prepared_data[field.name]
                for field in task.fields
                if field.name in data_preparer.prepared_data
            }
            # Add task function to callables?
            if isfunction(task.implementation):
                run_name = f' task "{task.name}" {task.full_name}'
                run_function = task.implementation
                run_calls.append((run_name, run_function, task_field_data))
            # Add class method(s) to callables?
            elif isclass(task.implementation):
                try:
                    # Instantiate the task handler class with required field data. Non-field
                    # data members and type mismatches may cause errors.
                    handler_instance = task.implementation(**task_field_data)
                    run_method = getattr(handler_instance, 'on_run', None)
                    if ismethod(run_method):
                        run_name = f' task "{task.name}" {task.full_name}.on_run()'
                        run_calls.append((run_name, run_method, {}))
                    done_method = getattr(handler_instance, 'on_done', None)
                    if ismethod(done_method):
                        done_name = f' task "{task.name}" {task.full_name}.on_done()'
                        done_calls.insert(0, (done_name, done_method, {}))
                except Exception as exc:
                    abort(f'Exception constructing task "{task.name}" class:',
                          task.full_name,
                          exc,
                          exception_traceback_skip=1)
        # Invoke run callable stack.
        # Invoke done callable stack (reverse of run callable order).
        for run_name, run_function, run_kwargs in run_calls:
            # noinspection PyBroadException
            try:
                run_function(runtime, **run_kwargs)
            except Exception as exc:
                abort(f'Exception invoking {run_name}.',
                      exc,
                      exception_traceback_skip=1)
        for done_name, done_function, done_kwargs in done_calls:
            # noinspection PyBroadException
            try:
                done_function(runtime, **done_kwargs)
            except Exception as exc:
                abort(f'Exception invoking {done_name}.',
                      exc,
                      exception_traceback_skip=1)
    except KeyboardInterrupt:
        sys.stdout.write(os.linesep)
    except ArgumentNameError as exc:
        abort(str(exc))
    except Exception as exc:
        active_names = [task_stack_item.name for task_stack_item in task_stack]
        abort(f'Task command failed:',
              ' '.join(active_names),
              exc,
              exception_traceback_skip=1)


def _populate_driver_task(driver_task: DriverTask,
                          fields: List[TaskField],
                          sub_tasks: List[AssignedTask],
                          ):
    for task_field in fields:
        driver_task.add_field(name=task_field.name,
                              description=task_field.description,
                              element_type=task_field.element_type,
                              hints=task_field.hints,
                              default=task_field.default,
                              repeat=task_field.repeat,
                              choices=task_field.choices)
    for sub_task in sub_tasks:
        driver_sub_task = driver_task.add_sub_task(sub_task.name,
                                                   sub_task.description,
                                                   sub_task.notes,
                                                   sub_task.footnotes,
                                                   sub_task.visibility)
        _populate_driver_task(driver_sub_task, sub_task.fields, sub_task.sub_tasks)


def _add_builtin_tasks(tool: Tool):
    visibility = 2 if tool.tool_options.hide_builtin_tasks else 1

    def _add_if_needed(name: Text, task_ref: Text):
        if f'{name}[s]' in tool.assigned_root_task.sub_tasks:
            return
        if f'{name}[h]' in tool.assigned_root_task.sub_tasks:
            return
        assigned_task = TASK_REGISTRY.resolve_assigned_task(task_ref, name, visibility)
        if assigned_task is not None:
            tool.assigned_root_task.sub_tasks.append(assigned_task)

    if not tool.tool_options.disable_help:
        _add_if_needed('help', 'jiig.tasks.help')
    if not tool.tool_options.disable_alias:
        _add_if_needed('alias', 'jiig.tasks.alias')
    if tool.venv_needed:
        _add_if_needed('venv', 'jiig.tasks.venv')


def main(tool: Tool,
         runner_args: List[Text] = None,
         cli_args: List[Text] = None,
         ):
    """
    Main function called from jiig-run to drive tool and task initialization.

    :param tool: registered tool configuration object
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

    # Construct the driver.
    supported_global_options: List[Text] = []
    if not tool.tool_options.disable_debug:
        supported_global_options.append('debug')
    if not tool.tool_options.disable_dry_run:
        supported_global_options.append('dry_run')
    if not tool.tool_options.disable_verbose:
        supported_global_options.append('verbose')
    if tool.tool_options.enable_pause:
        supported_global_options.append('pause')
    if tool.tool_options.enable_keep_files:
        supported_global_options.append('keep_files')
    driver_options = DriverOptions(
        variant=tool.driver_variant,
        raise_exceptions=True,
        top_task_label=TOP_TASK_LABEL,
        sub_task_label=SUB_TASK_LABEL,
        top_task_dest_name=TOP_TASK_DEST_NAME,
        supported_global_options=supported_global_options,
    )
    driver_registration = DRIVER_REGISTRY.resolve(tool.driver, required=True)
    driver = driver_registration.implementation(tool.tool_name,
                                                tool.description,
                                                options=driver_options)

    # Establish driver-supplied log writer to implement log output.
    set_log_writer(driver.get_log_writer())

    # Initialize the driver. Only display message once.
    driver_initialization_data = driver.initialize_driver(raw_arguments)
    if not tool.venv_active:
        log_message('Jiig driver initialized.', debug=True)

    # Initialize option settings, which are shared through the util library.
    OPTIONS.from_strings(driver.enabled_global_options)

    # Check if a virtual environment is required, but not active. If so, it
    # restarts inside the virtual environment (and does not return from call).
    _check_virtual_environment(runner_args, cli_args, tool)

    # Initialize the Python library load path.
    for lib_folder in reversed(tool.library_folders):
        if os.path.isdir(lib_folder) and lib_folder not in sys.path:
            sys.path.insert(0, lib_folder)

    # Resolve a custom runtime context class.
    if tool.runtime is not None:
        registered_runtime = CONTEXT_REGISTRY.resolve(tool.runtime, required=True)
        runtime_class = registered_runtime.implementation
    else:
        runtime_class = Runtime

    # Add automatic built-in secondary or hidden sub-tasks, if not disabled.
    have_tasks = bool(tool.assigned_root_task.sub_tasks)
    _add_builtin_tasks(tool)

    # Convert the runtime task hierarchy to a driver task hierarchy.
    # Add automatic secondary ('...[s]') sub-tasks, if not disabled.
    driver_root_task = DriverTask(name=tool.tool_name,
                                  description=tool.assigned_root_task.description,
                                  sub_tasks=[],
                                  fields=[],
                                  notes=tool.assigned_root_task.notes,
                                  footnotes=tool.assigned_root_task.footnotes,
                                  visibility=0)
    _populate_driver_task(driver_root_task,
                          tool.assigned_root_task.fields,
                          tool.assigned_root_task.sub_tasks)

    # Just display help if there sub-tasks and no arguments to process.
    if have_tasks and not driver_initialization_data.final_arguments:
        driver.provide_help(driver_root_task)
        sys.exit(0)

    driver_app_data = driver.initialize_application(driver_initialization_data,
                                                    driver_root_task)
    log_message('Application initialized.', debug=True)

    # Check hint usage.
    HINT_REGISTRY.add_supported_hints('repeat', 'choices', 'default')
    if driver.supported_hints:
        HINT_REGISTRY.add_supported_hints(*driver.supported_hints)
    bad_hints = HINT_REGISTRY.get_bad_hints()
    if bad_hints:
        log_error(f'Bad field {plural("hint", bad_hints)}:', *bad_hints)

    # Convert driver task stack to RegisteredTask stack.
    task_stack: List[AssignedTask] = [tool.assigned_root_task]
    for driver_task in driver_app_data.task_stack:
        for sub_task in task_stack[-1].sub_tasks:
            if sub_task.name == driver_task.name:
                task_stack.append(sub_task)
                break

    class HelpGenerator(RuntimeHelpGenerator):
        def generate_help(self, *names: Text, show_hidden: bool = False):
            driver.provide_help(driver_root_task, *names, show_hidden=show_hidden)

    # Create and initialize root Runtime context.
    runtime = runtime_class(None,
                            tool=tool,
                            help_generator=HelpGenerator(),
                            data=driver_app_data.data)

    log_message('Executing application...', debug=True)
    _execute(runtime, task_stack, driver_app_data.data)
