# Copyright (C) 2020-2022, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

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
from inspect import isfunction
from typing import List, Text, Callable, Tuple, Dict

from .driver import DriverOptions, DriverTask
from .registry import CONTEXT_REGISTRY, DRIVER_REGISTRY, HINT_REGISTRY, TASK_REGISTRY, \
    Runtime, RuntimeHelpGenerator, Tool, TaskField, AssignedTask, \
    SUB_TASK_LABEL, TOP_TASK_LABEL, TOP_TASK_DEST_NAME
from .util.exceptions import format_exception
from .util.log import abort, log_error, log_message, set_log_writer
from .util.options import OPTIONS
from .util.python import build_virtual_environment, PYTHON_NATIVE_ENVIRONMENT_NAME
from .util.text import plural


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
                            format_exception(exc, label=label, skip_frame_count=1))
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
        # Run functions are invoked outer to inner, and done functions, if
        # added, are invoked in reverse, inner to outer order. The string is the
        # name used for errors. The dict is for keyword call arguments (task
        # functions only).
        run_calls: List[Tuple[Text, Callable, Dict]] = []
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
                run_name = f'task "{task.name}" {task.full_name}'
                run_function = task.implementation
                run_calls.append((run_name, run_function, task_field_data))
        # Invoke run callable stack.
        for run_name, run_function, run_kwargs in run_calls:
            # noinspection PyBroadException
            try:
                log_message(f'Invoking {run_name}...', debug=True)
                run_function(runtime, **run_kwargs)
            except Exception as exc:
                abort(f'Exception invoking {run_name}.',
                      exc,
                      exception_traceback_skip=1)
        # Invoke done callable stack (reverse of run callable order).
        if runtime.when_done_callables:
            for done_call in runtime.when_done_callables:
                try:
                    # Takes no arguments, because callable supplier should
                    # capture necessary data in a closure or callable object.
                    done_call()
                except Exception as exc:
                    abort(f'Exception invoking clean-up call-back {done_call.__name__}.',
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
                              default=task_field.default,
                              repeat=task_field.repeat,
                              choices=task_field.choices)
    for sub_task in sub_tasks:
        driver_sub_task = driver_task.add_sub_task(sub_task.name,
                                                   sub_task.description,
                                                   sub_task.notes,
                                                   sub_task.footnotes,
                                                   sub_task.visibility,
                                                   sub_task.hints)
        _populate_driver_task(driver_sub_task, sub_task.fields, sub_task.sub_tasks)


def _add_builtin_tasks(tool: Tool):
    visibility = 2 if tool.tool_options.hide_builtin_tasks else 1
    root_task_names = set((sub_task.name for sub_task in tool.assigned_root_task.sub_tasks))

    def _add_if_needed(name: Text, task_ref: Text):
        if not root_task_names.intersection({name, f'{name}[s]', f'{name}[h]'}):
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
    Main function called from jiig script to drive tool and task initialization.

    :param tool: registered tool configuration object
    :param runner_args: optional Jiig runner preamble, e.g. for jiig shebang usage
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
    if not driver_initialization_data.final_arguments:
        driver_initialization_data.final_arguments = ['help']
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
    _add_builtin_tasks(tool)

    # Convert the runtime task hierarchy to a driver task hierarchy.
    driver_root_task = DriverTask(name=tool.tool_name,
                                  description=tool.assigned_root_task.description,
                                  sub_tasks=[],
                                  fields=[],
                                  notes=tool.assigned_root_task.notes,
                                  footnotes=tool.assigned_root_task.footnotes,
                                  visibility=0,
                                  hints=tool.assigned_root_task.hints)
    _populate_driver_task(driver_root_task,
                          tool.assigned_root_task.fields,
                          tool.assigned_root_task.sub_tasks)

    driver_app_data = driver.initialize_application(driver_initialization_data,
                                                    driver_root_task)
    log_message('Application initialized.', debug=True)

    # Check task hint usage.
    if driver.supported_task_hints:
        HINT_REGISTRY.add_supported_task_hints(*driver.supported_task_hints)
    bad_task_hints = HINT_REGISTRY.get_bad_task_hints()
    if bad_task_hints:
        log_error(f'Bad task {plural("hint", bad_task_hints)}:', *bad_task_hints)

    # Check field hint usage.
    HINT_REGISTRY.add_supported_field_hints('repeat', 'choices', 'default')
    if driver.supported_field_hints:
        HINT_REGISTRY.add_supported_field_hints(*driver.supported_field_hints)
    bad_field_hints = HINT_REGISTRY.get_bad_field_hints()
    if bad_field_hints:
        log_error(f'Bad field {plural("hint", bad_field_hints)}:', *bad_field_hints)

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
    def _create_runtime() -> Runtime:
        try:
            return runtime_class(None,
                                 tool=tool,
                                 help_generator=HelpGenerator(),
                                 data=driver_app_data.data)
        except Exception as exc:
            abort(f'Exception while creating runtime class {runtime_class.__name__}',
                  exc,
                  exception_traceback_skip=1)
    runtime = _create_runtime()

    log_message('Executing application...', debug=True)
    _execute(runtime, task_stack, driver_app_data.data)
