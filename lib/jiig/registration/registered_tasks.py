"""
RegisteredTask wraps a task class and adds finalized data.

Registration basically takes an input Task class and massages the data for
consumption by the runtime engine. It adds some data, converts Task module
references to Task class references, and finalizes options, paths, etc..
"""

from inspect import isclass
from typing import Type, Text, List, Dict, Union

from jiig.constants import TASK_MODULE_CLASS_NAME
from jiig.utility.console import abort, log_error
from jiig.utility.general import AttrDict, format_exception
from jiig.utility.help_formatter import HelpProvider

from .arguments import Opt, Arg
from .tasks import Task
from .registration_utilities import prepare_registered_text


class RegisteredTask:
    """
    A registered Task class and associated data.

    Presents normalized and finalized runtime data based on a Task class.
    """
    def __init__(self,
                 task_class: Type[Task],
                 is_secondary: bool,
                 is_hidden: bool,
                 ):
        text_results = prepare_registered_text(task_class.description,
                                               task_class.notes,
                                               getattr(task_class, '__doc__', None))
        self.description = text_results.description
        self.notes = text_results.notes
        self.is_secondary = is_secondary
        self.is_hidden = is_hidden
        # Copy some useful task class data members here.
        # RegisteredTask has separate options and arguments lists.
        self.opts: List[Opt] = []
        self.args: List[Arg] = []
        for arg in task_class.args:
            if isinstance(arg, Opt):
                self.opts.append(arg)
            elif isinstance(arg, Arg):
                self.args.append(arg)
            else:
                log_error(f'Task class has non-Arg/non-Opt item in `args` list.',
                          arg,
                          task_class=task_class.__name__,
                          module=task_class.__module__)
        self.footnotes = task_class.footnotes
        self.receive_trailing_arguments = task_class.receive_trailing_arguments
        # Prepare various flavors of sub-tasks.
        sub_task_preparer = self._SubTaskPreparer()
        sub_task_preparer.prepare(task_class.sub_tasks)
        sub_task_preparer.prepare(task_class.secondary_sub_tasks, is_secondary=True)
        sub_task_preparer.prepare(task_class.hidden_sub_tasks, is_hidden=True)
        if sub_task_preparer.resolution_errors:
            abort(f'Failed to register task modules and or classes.',
                  sub_task_preparer.resolution_errors)
        self.sub_tasks = sub_task_preparer.sub_tasks
        # Used by create_task()
        self._task_class = task_class

    def create_task(self,
                    name: Text,
                    params: AttrDict,
                    data: object,
                    trailing_arguments: List[Text],
                    help_provider: HelpProvider,
                    ) -> Task:
        """
        Create Task instance.

        :param name: required name
        :param params: configuration parameter data
        :param data: parsed command line arguments as object with data attributes
        :param trailing_arguments: command line trailing arguments, if requested
        :param help_provider: used for displaying help
        """
        return self._task_class(name, params, data, trailing_arguments, help_provider)

    class _SubTaskPreparer:

        def __init__(self):
            self.sub_tasks: Dict[Text, RegisteredTask] = {}
            self.resolution_errors: List[Text] = []

        def prepare_sub_task(self,
                             task_or_module: Union[Type['Task'], object],
                             name: Text,
                             is_secondary: bool = False,
                             is_hidden: bool = False,
                             ):
            if isclass(task_or_module):
                if issubclass(task_or_module, Task):
                    # It's the actual Task class.
                    task_class = task_or_module
                else:
                    self.resolution_errors.append(f'"{task_or_module.__class__.__name__}"'
                                                  f' is not a Task sub-class.')
                    return
            else:
                # Assume it's a module - look for the specially-named class.
                task_class = getattr(task_or_module, TASK_MODULE_CLASS_NAME, None)
                if task_class is None:
                    self.resolution_errors.append(f'No Task class was declared as'
                                                  f' "{TASK_MODULE_CLASS_NAME}".')
                    return
                if not issubclass(task_class, Task):
                    self.resolution_errors.append(f'"{TASK_MODULE_CLASS_NAME}" is not'
                                                  f' a Task sub-class.')
                    return
            self.sub_tasks[name] = RegisteredTask(task_class, is_secondary, is_hidden)

        def prepare(self,
                    raw_tasks: Dict[Text, Union[Type['Task'], object]],
                    is_secondary: bool = False,
                    is_hidden: bool = False,
                    ):
            for name, raw_task in raw_tasks.items():
                self.prepare_sub_task(raw_task,
                                      name,
                                      is_secondary=is_secondary,
                                      is_hidden=is_hidden)

    class ArgumentDataPreparationResults:
        """Results provided by prepare_argument_data()."""
        def __init__(self):
            self.errors: List[Text] = []

    def prepare_argument_data(self,
                              raw_data: object,
                              prepared_data: object,
                              ) -> ArgumentDataPreparationResults:
        """
        Convert raw argument data to prepared data.

        :param raw_data: raw input data
        :param prepared_data: output data to populate
        :return: results with error information
        """
        results = self.ArgumentDataPreparationResults()
        for args in (self.opts, self.args):
            for arg in args:
                if hasattr(raw_data, arg.name):
                    value = getattr(raw_data, arg.name)
                    adapter_name = '???'
                    try:
                        # Call all adapters to validate and convert as appropriate.
                        if value is not None:
                            for adapter in arg.adapters:
                                adapter_name = adapter.__name__
                                if arg.multi_value:
                                    value = [adapter(value_item) for value_item in value]
                                else:
                                    value = adapter(value)
                        setattr(prepared_data, arg.name, value)
                    except (TypeError, ValueError) as exc:
                        results.errors.append(
                            format_exception(exc,
                                             label=f'{arg.name}:{adapter_name}',
                                             skip_stack_levels=1))
        return results
