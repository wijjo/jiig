"""
Task class.

The Task class has raw data, as extracted from task modules or or user-defined
task classes. It should not be altered at runtime.
"""

# TODO: Derived task data is handled inefficiently. Access should be minimized
# unless a caching strategy is implemented.

import re
from dataclasses import dataclass, field
from importlib import import_module
from inspect import isfunction, signature
from types import ModuleType
from typing import Text, List, Dict, Union, Type, Tuple, Any, Optional, Sequence

from jiig import const
from jiig.arg import Choices, Default
from jiig.typing import OptionFlag, ArgumentAdapter, Cardinality, RunFunction, DoneFunction
from jiig.util.console import log_error, log_warning
from jiig.util.footnotes import NotesList, NotesDict

TASK_IDENT_REGEX = re.compile(r'^'
                              r'([a-zA-Z][a-zA-Z0-9\-_]*)'
                              r'(?:\[(s|secondary|h|hidden)\])?'
                              r'$')
ARG_IDENT_REGEX = re.compile(r'^'
                             r'([a-zA-Z][a-zA-Z0-9\-_]*)'
                             r'(?:\[(\d+|\*|\+|!|\?)\])?'
                             r'$')


class TaskFunctions:
    """Holds registered functions for a Task."""

    def __init__(self):
        self.run_functions: List[RunFunction] = []
        self.done_functions: List[DoneFunction] = []


@dataclass
class Task:
    """
    Task configuration class.

    Holds user-provided meta-data, with some members elaborated below.

    # Sub-task dictionaries (tasks).

    Maps sub-task <identifier> keys to task specifications.

    ## Task specification.

    A task specification can be one of the following.

    - Task instance
    - Task module
    - Task module name

    ## Task identifier.

    Task identifier format: "<name>[<modifier>]"

    ## Task modifier.

    - s or secondary: displayed in help secondary task list
    - h or hidden: hidden from help task lists unless (-a/--all) option is used

    # Argument dictionaries.

    Maps argument <identifier> keys to <specification> values.

    ## Argument identifier.

    format: "<name>[<modifier>]"

    ### Optional argument modifier.

    modifier format "[<value>]"

    Supported modifier values are:
    - number: a specific quantity
    - *: zero or more, with no upper limit
    - +: one or more, with no upper limit
    - ?: optional single argument
    - !: boolean, indicates flag options that need no value argument

    When a repetition modifier is specified argument data is provided as a list.

    ## <specification>

    The argument specification value can either be a string or a tuple.

    A string becomes the argument description, and the argument is configured as
    a simple text string.

    A tuple supports the following content to provide greater flexibility in
    defining arguments.

    - "-..." strings are taken as option flags. Without any flag strings, it is
      assumed to be a positional argument.
    - Any other text string is taken as the argument description.
    - Callable references are taken as argument data adapters.
    - A Choices object can define a limited value set for the argument.
    - A Default object can establish a default value if the argument is not
      provided on the command line.
    """

    description: Text = None
    """Task description."""

    notes: NotesList = None
    """Task help notes."""

    footnotes: NotesDict = field(default_factory=dict)
    """Named footnotes displayed in task help if referenced by "[<name>]"."""

    tasks: Dict[Text, Union[Type, Text, object]] = field(default_factory=dict)
    """Sub-task classes, modules, or module full name, by name."""

    args: Dict[Text, Union[Text, Tuple]] = field(default_factory=dict)
    """Argument/option definition dictionary."""

    receive_trailing_arguments: bool = False
    """Keep unparsed trailing arguments if True."""

    def __post_init__(self):
        self.functions = TaskFunctions()

    def run(self, run_function: RunFunction) -> RunFunction:
        self.functions.run_functions.append(run_function)
        return run_function

    def done(self, done_function: DoneFunction) -> DoneFunction:
        self.functions.done_functions.append(done_function)
        return done_function


@dataclass
class FlaggedOption:
    """Flagged option data."""
    name: Text
    flags: List[OptionFlag]
    description: Text
    adapters: List[ArgumentAdapter] = None
    cardinality: Cardinality = None
    default_value: Any = None
    choices: List = None
    is_boolean: bool = False


@dataclass
class PositionalArgument:
    """Positional argument data."""
    name: Text
    description: Text
    adapters: List[ArgumentAdapter] = None
    cardinality: Cardinality = None
    default_value: Any = None
    choices: List = None


@dataclass
class TaskArguments:
    """Flagged options and positional arguments."""
    flagged_options: List[FlaggedOption] = field(default_factory=list)
    positional_arguments: List[PositionalArgument] = field(default_factory=list)


class TaskRuntime:
    """Wrapper for user Task configuration that provides final Task runtime data."""

    def __init__(self, task: Task, name: Text, visibility: int):
        self._task = task
        self._name = name
        self._visibility = visibility
        # Produced on-demand.
        self._arguments: Optional[TaskArguments] = None
        self._sub_tasks: Optional[List[TaskRuntime]] = None

    @property
    def name(self) -> Text:
        """
        Task name.

        :return: task name
        """
        return self._name

    @property
    def visibility(self) -> int:
        """
        Help visibility, 0=primary, 1=secondary, 2=hidden.

        :return: visibility integer value
        """
        return self._visibility

    @property
    def description(self) -> Text:
        """
        Task description.

        :return: task description
        """
        return self._task.description or '(no description)'

    @property
    def notes(self) -> NotesList:
        """
        Task help notes.

        :return: note list
        """
        return self._task.notes or []

    @property
    def footnotes(self) -> NotesDict:
        """
        Named footnotes displayed in task help if referenced by "[<name>]".

        :return: footnote dictionary
        """
        return self._task.footnotes or {}

    @property
    def run_functions(self) -> List[RunFunction]:
        """
        Read-only access to registered @run function list.

        These functions are called to perform task operations.

        :return: registered @run function list
        """
        return self._task.functions.run_functions

    @property
    def done_functions(self) -> List[DoneFunction]:
        """
        Read-only access to registered @done function list.

        These functions are called after after sub-tasks complete just before
        the program exists. It is a clean-up opportunity.

        :return: registered @done function list
        """
        return self._task.functions.done_functions

    @property
    def flagged_options(self) -> List[FlaggedOption]:
        """
        Flagged option list.

        Built on-demand.

        :return: flagged option list
        """
        if self._arguments is None:
            self._populate_arguments()
        return self._arguments.flagged_options

    @property
    def positional_arguments(self) -> List[PositionalArgument]:
        """
        Positional argument list.

        Built on-demand.

        :return: Positional argument list
        """
        if self._arguments is None:
            self._populate_arguments()
        return self._arguments.positional_arguments

    @property
    def sub_tasks(self) -> List['TaskRuntime']:
        """
        Produce a sub-task list, with added name and visibility.

        :return: sub-task list
        """
        if self._sub_tasks is None:
            self._sub_tasks: List[TaskRuntime] = []
            for ident, spec in self._task.tasks.items():
                ident_match = TASK_IDENT_REGEX.match(ident)
                if ident_match is None:
                    log_error(f'Bad task identifier "{ident}".')
                    continue
                name = ident_match.group(1)
                visibility_spec = ident_match.group(2).lower() if ident_match.group(2) else ''
                if visibility_spec in ['s', 'secondary']:
                    visibility = 1
                elif visibility_spec in ['h', 'hidden']:
                    visibility = 2
                else:
                    visibility = 0
                task = self.resolve_task_spec(spec, name, visibility)
                if task is None:
                    continue
                self._sub_tasks.append(task)
        return self._sub_tasks

    @property
    def receive_trailing_arguments(self) -> bool:
        """
        Indicates that this task consumes trailing arguments.

        :return: True if trailing arguments are consumed by this task
        """
        return self._task.receive_trailing_arguments

    def _populate_arguments(self):
        self._arguments = TaskArguments()
        for ident, spec in self._task.args.items():
            errors: List[Text] = []
            opt_or_arg = self._get_opt_or_arg(ident, spec, errors)
            if opt_or_arg is None:
                log_error(f'Bad task option/argument "{ident}".', spec, *errors)
                continue
            if isinstance(opt_or_arg, FlaggedOption):
                self._arguments.flagged_options.append(opt_or_arg)
            elif isinstance(opt_or_arg, PositionalArgument):
                self._arguments.positional_arguments.append(opt_or_arg)
            else:
                assert 'Unexpected return from _get_opt_or_arg().'

    @staticmethod
    def _get_opt_or_arg(opt_or_arg_ident: Text,
                        opt_or_arg_spec: Any,
                        errors: List[Text],
                        ) -> Optional[Union['FlaggedOption', 'PositionalArgument']]:
        flags: Optional[List[OptionFlag]] = None
        descriptions: List[Text] = []
        adapters: Optional[List[ArgumentAdapter]] = None
        cardinality: Optional[Cardinality] = None
        default_value: Optional[Any] = None
        choices: Optional[List] = None
        parsed_name = ARG_IDENT_REGEX.match(opt_or_arg_ident)
        is_boolean = False
        if not parsed_name:
            errors.append('Bad argument identifier.')
            return None
        arg_name = parsed_name.group(1)
        modifier = parsed_name.group(2)
        if modifier:
            if modifier[0].isdigit():
                cardinality = int(modifier)
            elif modifier == '!':
                is_boolean = True
            else:
                cardinality = modifier
        if isinstance(opt_or_arg_spec, str):
            descriptions.append(opt_or_arg_spec)
        elif isinstance(opt_or_arg_spec, tuple):
            for item_idx, item in enumerate(opt_or_arg_spec):
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
                        errors.append(f'Adapter function {item.__name__}'
                                      f' missing value parameter.')
                    else:
                        adapters.append(item)
                elif isinstance(item, Choices):
                    choices = list(item.values)
                elif isinstance(item, Default):
                    default_value = item.value
                else:
                    errors.append(f'Bad argument tuple item (#{item_idx + 1}): {item}')
                    return
        if len(descriptions) == 0:
            description = '(no description)'
        else:
            if len(descriptions) > 1:
                errors.append('Too many description strings for argument.')
            description = descriptions[-1]
        if flags is not None:
            return FlaggedOption(arg_name,
                                 flags,
                                 description,
                                 adapters=adapters,
                                 cardinality=cardinality,
                                 default_value=default_value,
                                 choices=choices,
                                 is_boolean=is_boolean)
        if is_boolean:
            log_warning(f'Ignoring "!" modifier for positional argument'
                        f' "{opt_or_arg_ident}".')
        return PositionalArgument(arg_name,
                                  description,
                                  adapters=adapters,
                                  cardinality=cardinality,
                                  default_value=default_value,
                                  choices=choices)

    @classmethod
    def resolve_task_spec(cls,
                          spec: Any,
                          name: Text,
                          visibility: int,
                          ) -> Optional['TaskRuntime']:
        """
        Resolve task specification to a Task object.

        Displays appropriate error message when it does not resolve. So the
        caller just needs to check for None and act accordingly.

        :param spec: Task instance, module, or module name
        :param name: task name
        :param visibility: help visibility, 0=primary, 1=secondary, 2=hidden
        :return:
        """
        # Task object?
        if isinstance(spec, Task):
            return cls(spec, name, visibility)
        # Either a module or module name...
        if isinstance(spec, str):
            # Import task module by name.
            try:
                # Load module by name and resolve it to a Task object below.
                module = import_module(spec)
                display_name = spec
            except Exception as exc:
                log_error(f'Failed to import task module by name.', spec, exc)
                return None
        else:
            # Assume it's a task module and resolve it to a Task object below.
            module = spec
            display_name = getattr(module, '__name__', str(spec))
        return cls._resolve_task_module(module, name, visibility, display_name)

    @classmethod
    def _resolve_task_module(cls,
                             module: ModuleType,
                             name: Text,
                             visibility: int,
                             display_name: Text,
                             ) -> Optional['TaskRuntime']:
        task_obj = getattr(module, const.TASK_MODULE_GLOBAL_NAME, None)
        if task_obj is None:
            log_error(f'Task module "{display_name}" has no global'
                      f' "{const.TASK_MODULE_GLOBAL_NAME}" Task instance.')
            return None
        if not isinstance(task_obj, Task):
            log_error(f'Task module "{display_name}" global'
                      f' "{const.TASK_MODULE_GLOBAL_NAME}" is not a Task.')
            return None
        return cls(task_obj, name, visibility)

    @classmethod
    def _get_sub_task_stack(cls,
                            task: 'TaskRuntime',
                            names: Sequence[Text],
                            ) -> List['TaskRuntime']:
        for sub_task in task.sub_tasks:
            if sub_task.name == names[0]:
                if len(names) == 1:
                    return [sub_task]
                return [sub_task] + cls._get_sub_task_stack(sub_task, names[1:])
        raise ValueError(names[0])

    def get_task_stack(self, names: Sequence[Text]) -> List['TaskRuntime']:
        """
        Get TaskRuntime stack as list based on names list.

        :param names: name stack as list
        :return: sub-task stack as list
        :raise ValueError: if stack cannot be fully resolved
        """
        try:
            return self._get_sub_task_stack(self, names)
        except ValueError as exc:
            # Wrap the exception to add the entire command string.
            raise ValueError(f'Failed to resolve command "{str(exc)}"'
                             f' in command: {" ".join(names)}')
