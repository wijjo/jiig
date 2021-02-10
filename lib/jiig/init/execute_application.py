"""
Task execution initialization.
"""

from typing import List, Text

from jiig import model
from jiig.typing import Cardinality
from jiig.util.console import abort
from jiig.util.general import format_exception

from .load_application import ApplicationData


class ArgumentNameError(RuntimeError):
    pass


class PreparedArgumentData:
    """A blank object that receives argument data as attributes."""

    def __getattr__(self, name):
        """
        Provide a better error for bad attribute names.

        :param name: attribute name
        :return: attribute value
        """
        if name not in self.__dict__:
            raise ArgumentNameError(f'Command argument data has no "{name}" attribute.')
        return super().__getattr__(name)


class _ArgumentDataPreparer:

    def __init__(self, raw_data: object):
        self.raw_data = raw_data
        self.prepared_data = PreparedArgumentData()
        self.errors: List[Text] = []

    @staticmethod
    def _is_multi_value(cardinality: Cardinality = None) -> bool:
        if cardinality is not None:
            if isinstance(cardinality, int):
                return cardinality > 1
            if cardinality in ('*', '+'):
                return True
        return False

    def prepare_argument_data(self, task_runtime: model.TaskRuntime):
        # Convert raw argument data to prepared data.
        for args_opts in (task_runtime.flagged_options,
                          task_runtime.positional_arguments):
            for arg_opt in args_opts:
                if hasattr(self.raw_data, arg_opt.name):
                    value = getattr(self.raw_data, arg_opt.name)
                    adapter_name = '???'
                    try:
                        # Call all adapters to validate and convert as appropriate.
                        if value is not None:
                            if arg_opt.adapters is not None:
                                for adapter in arg_opt.adapters:
                                    adapter_name = adapter.__name__
                                    if self._is_multi_value(arg_opt.cardinality):
                                        value = [adapter(value_item) for value_item in value]
                                    else:
                                        value = adapter(value)
                        setattr(self.prepared_data, arg_opt.name, value)
                    except (TypeError, ValueError) as exc:
                        self.errors.append(
                            format_exception(exc,
                                             label=f'{arg_opt.name}:{adapter_name}',
                                             skip_stack_levels=1))


def go(application_data: ApplicationData):
    """
    Initialize tool execution.

    :param application_data: application runtime data
    """
    # Prepare argument data using raw data and task option/argument definitions.
    data_preparer = _ArgumentDataPreparer(application_data.data)
    for task_runtime in application_data.active_task_stack:
        data_preparer.prepare_argument_data(task_runtime)
    if len(data_preparer.errors) > 0:
        abort(f'{len(data_preparer.errors)} argument failure(s):', *data_preparer.errors)

    try:
        # Invoke task stack @run call-backs in top to bottom order.
        for task_runtime in application_data.active_task_stack:
            for run_function in task_runtime.run_functions:
                run_function(application_data.runner, data_preparer.prepared_data)
        # Invoke task stack @done call-backs in reverse order.
        for task_runtime in reversed(application_data.active_task_stack):
            for done_function in task_runtime.done_functions:
                done_function(application_data.runner, data_preparer.prepared_data)
    except KeyboardInterrupt:
        print('')
    except ArgumentNameError as exc:
        abort(str(exc))
    except Exception as exc:
        abort(f'Task command failed:', ' '.join(application_data.active_names), exc)
