"""
RegisteredTask wraps a task class and adds finalized data.

Registration basically takes an input Task class and massages the data for
consumption by the runtime engine. It adds some data, converts Task module
references to Task class references, and finalizes options, paths, etc..
"""

import re
from copy import copy
from inspect import isclass, isfunction, signature
from typing import Type, Text, List, Dict, Union, Any, Sequence, Optional

from jiig import const
from jiig.arg import Choices, Default
from jiig.typing import ArgumentAdapter, Cardinality, OptionFlag
from jiig.util.console import abort, log_error
from jiig.util.general import format_exception
from jiig.util.help_formatter import HelpProvider

from jiig.obsolete._util import prepare_registered_text
from .registered_argument import RegisteredArgument
from .registered_option import RegisteredOption
from jiig.model.app_runtime import AppRuntime
from jiig.config.task import TaskOptions, Task


ARGUMENT_NAME_REGEX = re.compile(r'^([a-zA-Z][a-zA-Z0-9\-_]*)((?:\[(?:\d+|\*|\+)\])|!|\?)?$')


def _is_multi_value(cardinality: Cardinality = None) -> bool:
    if cardinality is not None:
        if isinstance(cardinality, int):
            return cardinality > 1
        if cardinality in ('*', '+'):
            return True
    return False


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
        self.opts: List[RegisteredOption] = []
        self.args: List[RegisteredArgument] = []
        for arg_name, arg_obj in task_class.args.items():
            arg_or_opt = self._interpret_argument_data(task_class, arg_name, arg_obj)
            if isinstance(arg_or_opt, RegisteredOption):
                self.opts.append(arg_or_opt)
            elif isinstance(arg_or_opt, RegisteredArgument):
                self.args.append(arg_or_opt)
        self.footnotes = task_class.footnotes
        # Copy options.
        self.options = self._prepare_registered_task_options(task_class)
        # Prepare various flavors of sub-tasks.
        sub_task_preparer = self._SubTaskPreparer()
        sub_task_preparer.prepare(task_class.tasks)
        sub_task_preparer.prepare(task_class.secondary_tasks, is_secondary=True)
        sub_task_preparer.prepare(task_class.hidden_tasks, is_hidden=True)
        if sub_task_preparer.resolution_errors:
            abort(f'Failed to register task modules and or classes.',
                  *sub_task_preparer.resolution_errors)
        self.sub_tasks = sub_task_preparer.sub_tasks
        # Used by create_task()
        self._task_class = task_class

    @staticmethod
    def _prepare_registered_task_options(source_task_class: Type[Task]) -> TaskOptions:
        return TaskOptions(
            pip_packages=copy(source_task_class.options.pip_packages),
            receive_trailing_arguments=source_task_class.options.receive_trailing_arguments,
        )

    @staticmethod
    def _interpret_argument_data(task_class: Type[Task],
                                 name: Text,
                                 data: Any,
                                 ) -> Optional[Union[RegisteredArgument,
                                                     RegisteredOption]]:
        def _error(message: Text, *args):
            log_error(message,
                      *args,
                      argument_name=name,
                      task_class=task_class.__name__,
                      module=task_class.__module__)
        flags: Optional[List[OptionFlag]] = None
        descriptions: List[Text] = []
        adapters: Optional[List[ArgumentAdapter]] = None
        cardinality: Optional[Cardinality] = None
        default_value: Optional[Any] = None
        choices: Optional[Sequence] = None
        parsed_name = ARGUMENT_NAME_REGEX.match(name)
        is_boolean = False
        if not parsed_name:
            _error(f'Bad argument name.')
            return None
        arg_name = parsed_name.group(1)
        modifier = parsed_name.group(2)
        if modifier:
            if modifier.startswith('['):
                cardinality = modifier[1:-1]
                if cardinality[0].isdigit():
                    cardinality = int(cardinality)
            elif modifier == '!':
                is_boolean = True
            elif modifier == '?':
                cardinality = '?'
        if isinstance(data, str):
            descriptions.append(data)
        elif isinstance(data, tuple):
            for item_idx, item in enumerate(data):
                if isinstance(item, str):
                    if item.startswith('-'):
                        if flags is None:
                            flags = []
                        flags.append(item)
                    else:
                        descriptions.append(item)
                elif item in (int, bool, float, str):
                    pass
                elif isfunction(item):
                    if adapters is None:
                        adapters = []
                    sig = signature(item)
                    if not sig.parameters:
                        _error('Adapter function missing value parameter.',
                               item.__name__)
                    else:
                        adapters.append(item)
                elif isinstance(item, Choices):
                    choices = item.values
                elif isinstance(item, Default):
                    default_value = item.value
                else:
                    _error(f'Bad argument tuple item (#{item_idx + 1}).', str(item))
                    return None
        if len(descriptions) == 0:
            description = '(no description)'
        else:
            if len(descriptions) > 1:
                _error('Too many description strings for argument.')
            description = descriptions[-1]
        if flags is not None:
            return RegisteredOption(arg_name,
                                    flags,
                                    description,
                                    adapters=adapters,
                                    cardinality=cardinality,
                                    default_value=default_value,
                                    choices=choices,
                                    is_boolean=is_boolean)
        if is_boolean:
            _error(f'Ignoring "!" modifier for positional argument.')
        return RegisteredArgument(arg_name,
                                  description,
                                  adapters=adapters,
                                  cardinality=cardinality,
                                  default_value=default_value,
                                  choices=choices)

    def create_task(self,
                    name: Text,
                    configuration: ToolConfiguration,
                    runtime_options: AppRuntime,
                    data: object,
                    trailing_arguments: List[Text],
                    help_provider: HelpProvider,
                    ) -> Task:
        """
        Create Task instance.

        :param name: required name
        :param configuration: tool configuration data
        :param runtime_options: runtime options
        :param data: parsed command line arguments as object with data attributes
        :param trailing_arguments: command line trailing arguments, if requested
        :param help_provider: used for displaying help
        """
        return self._task_class(name,
                                configuration,
                                runtime_options,
                                data,
                                trailing_arguments,
                                help_provider,
                                self.is_secondary,
                                )

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
                task_class = getattr(task_or_module, const.TASK_MODULE_CLASS_NAME, None)
                if task_class is None:
                    self.resolution_errors.append(
                        f'Module "{name}" has no Task class'
                        f' declared as "{const.TASK_MODULE_CLASS_NAME}".')
                    return
                if not issubclass(task_class, Task):
                    self.resolution_errors.append(
                        f'Module "{name}" "{const.TASK_MODULE_CLASS_NAME}"'
                        f' is not a Task sub-class.')
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
        for args_opts in (self.opts, self.args):
            for arg_opt in args_opts:
                if hasattr(raw_data, arg_opt.name):
                    value = getattr(raw_data, arg_opt.name)
                    adapter_name = '???'
                    try:
                        # Call all adapters to validate and convert as appropriate.
                        if value is not None:
                            if arg_opt.adapters is not None:
                                for adapter in arg_opt.adapters:
                                    adapter_name = adapter.__name__
                                    if _is_multi_value(arg_opt.cardinality):
                                        value = [adapter(value_item) for value_item in value]
                                    else:
                                        value = adapter(value)
                        setattr(prepared_data, arg_opt.name, value)
                    except (TypeError, ValueError) as exc:
                        results.errors.append(
                            format_exception(exc,
                                             label=f'{arg_opt.name}:{adapter_name}',
                                             skip_stack_levels=1))
        return results
