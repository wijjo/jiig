# Copyright (C) 2020-2023, Steven Cooper
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
from typing import Callable

from jiig.runtime import Runtime
from jiig.runtime_task import RuntimeTask
from jiig.util.exceptions import format_exception
from jiig.util.log import abort, log_message
from jiig.util.options import OPTIONS


class ArgumentNameError(RuntimeError):
    pass


class _ArgumentDataPreparer:

    def __init__(self, raw_data: object):
        self.raw_data = raw_data
        self.prepared_data = {}
        self.errors: list[str] = []

    def prepare_argument_data(self, task: RuntimeTask):
        # Convert raw argument data to prepared data.
        # Handle lower and upper case attribute names in raw data.
        for registered_field in task.fields:
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
                        label = ':'.join(
                            [
                                task.full_name,
                                arg_name,
                                f'adapter={adapter_name}',
                            ],
                        )
                        error = format_exception(exc, label=label, skip_frame_count=1)
                        self.errors.append(error)
                    else:
                        self.errors.append(f'{arg_name}: {str(exc)}')


def execute_application(task_stack: list[RuntimeTask],
                        argument_data: object,
                        runtime: Runtime,
                        ):
    """
    Run application.

    :param task_stack: task stack
    :param argument_data: argument data
    :param runtime: runtime interface
    """
    log_message('Executing application...', debug=True)
    # Prepare argument data using raw data and task option/argument definitions.
    data_preparer = _ArgumentDataPreparer(argument_data)
    for task in task_stack:
        data_preparer.prepare_argument_data(task)
    if len(data_preparer.errors) > 0:
        abort(f'Argument failures: {len(data_preparer.errors)}',
              *data_preparer.errors)
    try:
        # Run functions are invoked outer to inner, and done functions, if
        # added, are invoked in reverse, inner to outer order. The string is the
        # name used for errors. The dict is for keyword call arguments (task
        # functions only).
        run_calls: list[tuple[str, Callable, dict]] = []
        for task in task_stack:
            # Extract the data needed to populate task dataclass fields.
            # noinspection PyDataclass
            task_field_data = {
                field.name: data_preparer.prepared_data[field.name]
                for field in task.fields
                if field.name in data_preparer.prepared_data
            }
            # Add task function to callables?
            if isfunction(task.task_function):
                run_name = f'task "{task.name}" {task.full_name}'
                run_function = task.task_function
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
        active_names = [
            task_stack_item.name
            for task_stack_item in task_stack
        ]
        abort(f'Task command failed:',
              ' '.join(active_names),
              exc,
              exception_traceback_skip=1)
