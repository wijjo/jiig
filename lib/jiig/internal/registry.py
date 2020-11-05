"""Task and associated tool data registry."""
from dataclasses import dataclass
from typing import Text, Optional, List, Dict, Set, Iterator, Type, Any, Sequence

from jiig.internal.globals import tool_options
from jiig.internal.constants import HelpTaskVisibility
from jiig.internal.mapped_argument import MappedArgument, MappedArgumentList
from jiig.internal.mapped_task import MappedTask
from jiig.external.typing import ArgName, Description, \
    ArgumentTypeFactoryFunction, ArgumentTypeConversionFunction
from jiig.external.task_runner import RunnerFactoryFunction, TaskFunction, TaskFunctionsSpec
from jiig.utility.cli import make_dest_name, make_metavar
from jiig.utility.console import abort
from jiig.utility.footnotes import FootnoteDict, NotesSpec
from jiig.utility.general import make_list


# === Registered data


@dataclass
class RegisteredArgumentTypeFactoryFunction:
    """Saved data for argument type factory function."""
    function: ArgumentTypeFactoryFunction


@dataclass
class RegisteredArgumentTypeConversionFunction:
    """Saved data for argument type conversion function."""
    function: ArgumentTypeConversionFunction
    type_cls: Type
    default_value: Optional[Any]


class _RegisteredData:

    # Runner factory registered by @runner_factory decorator. Last registered one wins.
    runner_factory: Optional[RunnerFactoryFunction] = None

    # All registered mapped tasks.
    mapped_tasks: List[MappedTask] = []

    # To help map task name in command line arguments to MappedTask by argparse destination names.
    mapped_tasks_by_dest_name: Dict[Text, MappedTask] = {}

    # For quick lookups of parent and dependency tasks while processing @task decorator calls.
    mapped_tasks_by_id: Dict[int, MappedTask] = {}

    # Names of tasks that are only shown when the ALL_TASKS option is used for help.
    hidden_task_names: Set[Text] = set()

    # Argument type factory functions.
    argument_type_factories: Dict[int, RegisteredArgumentTypeFactoryFunction] = {}

    # Argument type conversion functions.
    argument_type_conversions: Dict[int, RegisteredArgumentTypeConversionFunction] = {}


def register_argument_type_factory(function: ArgumentTypeFactoryFunction):
    reg_obj = RegisteredArgumentTypeFactoryFunction(function)
    _RegisteredData.argument_type_factories[id(function)] = reg_obj


def register_argument_type(function: ArgumentTypeConversionFunction,
                           type_cls: Type,
                           default_value: Any = None):
    reg_obj = RegisteredArgumentTypeConversionFunction(function, type_cls, default_value)
    _RegisteredData.argument_type_conversions[id(function)] = reg_obj


def get_tool_tasks(include_hidden: bool = False) -> Iterator[MappedTask]:
    """
    Yield primary tasks (unsorted).

    :param include_hidden: include hidden task names if True
    :return: iterable MappedTask objects
    """
    for mt in _RegisteredData.mapped_tasks:
        if not mt.parent:
            if include_hidden or mt.name not in _RegisteredData.hidden_task_names:
                yield mt


def register_tool(name: Text = None,
                  description: Text = None,
                  notes: NotesSpec = None,
                  disable_alias: bool = None,
                  disable_help: bool = None,
                  disable_debug: bool = None,
                  disable_dry_run: bool = None,
                  disable_verbose: bool = None,
                  common_footnotes: FootnoteDict = None):
    # Only set values for the keywords that were provided.
    if name is not None:
        tool_options.set_name(name)
    if description is not None:
        tool_options.set_description(description)
    if notes:
        tool_options.set_notes(make_list(notes))
    if disable_alias is not None:
        tool_options.set_disable_alias(disable_alias)
    if disable_help is not None:
        tool_options.set_disable_help(disable_help)
    if disable_debug is not None:
        tool_options.set_disable_debug(disable_debug)
    if disable_dry_run is not None:
        tool_options.set_disable_dry_run(disable_dry_run)
    if disable_verbose is not None:
        tool_options.set_disable_verbose(disable_verbose)
    if common_footnotes is not None:
        tool_options.set_common_footnotes(common_footnotes)


class _MappedTaskMerger:
    def __init__(self, task_function: Optional[TaskFunction], arguments: Sequence[MappedArgument]):
        self.task_function = task_function
        self.arguments: MappedArgumentList = list(arguments)
        self.execution_tasks: List[MappedTask] = []
        self.parent_mapped_task: Optional[MappedTask] = None
        self.footnote_labels: List[Text] = []
        # Data to be finalized before creating the mapped task.
        self.task_name: Optional[Text] = None
        self.dest_name: Optional[Text] = None
        self.metavar: Optional[Text] = None
        self.description: Optional[Text] = None
        self.help_visibility = HelpTaskVisibility.NORMAL
        # Data used during merge processing.
        self._unique_dest_names: Set[Text] = set()
        self._unique_function_ids: Set[int] = set()

    @staticmethod
    def get_mapped_task(task_function: Optional[TaskFunction]
                        ) -> Optional[MappedTask]:
        if not task_function:
            return None
        mapped_task = _RegisteredData.mapped_tasks_by_id.get(id(task_function))
        if not mapped_task:
            abort('Unmapped task for function:', f'{task_function.__name__}()')
        return mapped_task

    class ArgumentMergeError(Exception):
        pass

    def merge_parent(self, parent_task_function: TaskFunction):
        self.parent_mapped_task = self.get_mapped_task(parent_task_function)
        if self.parent_mapped_task:
            if self.parent_mapped_task.execution_tasks:
                for parent_execution_task in self.parent_mapped_task.execution_tasks:
                    self.execution_tasks.append(parent_execution_task)
                    self._unique_function_ids.add(id(parent_execution_task.task_function))
            self.execution_tasks.append(self.parent_mapped_task)
            self._unique_function_ids.add(id(self.parent_mapped_task.task_function))

    def merge_dependencies(self, dependencies: Optional[List[TaskFunction]]):
        if dependencies:
            # Recursion is not needed since related tasks were already rolled up.
            for dependency_function in dependencies:
                dependency_function_id = id(dependency_function)
                if dependency_function_id in self._unique_function_ids:
                    continue
                dependency_mapped_task = _RegisteredData.mapped_tasks_by_id.get(
                    dependency_function_id, None)
                if not dependency_mapped_task:
                    continue
                # Execution tasks property yields child tasks and the parent task.
                for dependency_execution_task in dependency_mapped_task.execution_tasks:
                    dependency_execution_function_id = id(dependency_execution_task.task_function)
                    if dependency_execution_function_id in self._unique_function_ids:
                        continue
                    self.execution_tasks.append(dependency_execution_task)
                    self._unique_function_ids.add(dependency_execution_function_id)
                self.execution_tasks.append(dependency_mapped_task)
                self._unique_function_ids.add(dependency_function_id)

    def finalize_data(self,
                      name: Optional[Text],
                      description: Optional[Text],
                      hidden_task: Optional[bool],
                      auxiliary_task: Optional[bool]):

        # Generate the task name.
        if name:
            self.task_name = name
        else:
            if self.task_function.__name__.startswith('_'):
                abort(f'Private @task function "{self.task_function.__name__}()"'
                      f' has no name attribute.')
            self.task_name = self.task_function.__name__

        # Generate the dest and metavar names for argparse.
        names = []
        container_mapped_task = self.parent_mapped_task
        while container_mapped_task:
            names.append(container_mapped_task.name.upper())
            container_mapped_task = container_mapped_task.parent
        names.append(self.task_name.upper())
        self.dest_name = make_dest_name(*names)
        self.metavar = make_metavar(*names)

        # Generate the description.
        self.description = description.strip() if description else ''
        if not self.description:
            self.description = '(no description in @task decorator or doc string)'

        # Build final options and arguments by merging in ones from related tasks.
        for execution_task in self.execution_tasks:
            if execution_task.arguments:
                if execution_task.arguments:
                    for argument in execution_task.arguments:
                        if argument.flags:
                            if list(filter(lambda f: not isinstance(f, str), argument.flags)):
                                raise self.ArgumentMergeError(
                                    f'Option flag(s) ({argument.flags}) are not all strings.')
                        if argument.name not in self._unique_dest_names:
                            self.arguments.append(argument)
                            self._unique_dest_names.add(argument.name)

        # Derive the help visibility from the auxiliary and hidden flags
        if hidden_task:
            self.help_visibility = HelpTaskVisibility.HIDDEN
        elif auxiliary_task:
            self.help_visibility = HelpTaskVisibility.AUXILIARY


def register_task(task_function: TaskFunction,
                  name: ArgName = None,
                  parent: TaskFunction = None,
                  description: Description = None,
                  arguments: Sequence[MappedArgument] = None,
                  dependencies: TaskFunctionsSpec = None,
                  receive_trailing_arguments: bool = False,
                  notes: NotesSpec = None,
                  footnotes: FootnoteDict = None,
                  hidden_task: bool = False,
                  auxiliary_task: bool = False):

    # Merge and generate all the data needed for creating a mapped task.
    mt_data = _MappedTaskMerger(task_function, arguments)
    mt_data.merge_parent(parent)
    mt_data.merge_dependencies(dependencies)
    mt_data.finalize_data(name, description, hidden_task, auxiliary_task)

    # Create new mapped task using input and prepared data.
    mapped_task = MappedTask(task_function=task_function,
                             name=mt_data.task_name,
                             parent=mt_data.parent_mapped_task,
                             dest_name=mt_data.dest_name,
                             metavar=mt_data.metavar,
                             description=mt_data.description,
                             arguments=mt_data.arguments,
                             notes=make_list(notes),
                             footnotes=footnotes,
                             receive_trailing_arguments=receive_trailing_arguments,
                             execution_tasks=mt_data.execution_tasks,
                             help_visibility=mt_data.help_visibility)

    # Cascade trailing arguments flag upwards to signal need for capture.
    if receive_trailing_arguments:
        stack_mapped_task = mapped_task
        while stack_mapped_task:
            stack_mapped_task.capture_trailing_arguments = True
            stack_mapped_task = stack_mapped_task.parent

    # Register new MappedTask into global data structures.
    _RegisteredData.mapped_tasks_by_id[id(mapped_task.task_function)] = mapped_task
    if mapped_task.dest_name:
        _RegisteredData.mapped_tasks_by_dest_name[mapped_task.dest_name] = mapped_task
    if mapped_task.help_visibility == HelpTaskVisibility.HIDDEN:
        _RegisteredData.hidden_task_names.add(mapped_task.name)

    # Attach to parent sub-tasks or register globally if there is no parent.
    if mapped_task.parent:
        if mapped_task.parent.sub_tasks is None:
            mapped_task.parent.sub_tasks = []
        mapped_task.parent.sub_tasks.append(mapped_task)
    else:
        _RegisteredData.mapped_tasks.append(mapped_task)
    return mapped_task


def register_runner_factory(runner_factory: RunnerFactoryFunction):
    _RegisteredData.runner_factory = runner_factory


def get_runner_factory() -> Optional[RunnerFactoryFunction]:
    return _RegisteredData.runner_factory


def get_sorted_named_mapped_tasks() -> List[MappedTask]:
    return sorted(filter(lambda m: m.name, _RegisteredData.mapped_tasks),
                  key=lambda m: m.name)


def get_mapped_task_by_dest_name(dest_name: Text) -> Optional[MappedTask]:
    return _RegisteredData.mapped_tasks_by_dest_name.get(dest_name)


def get_argument_type_factory(function: ArgumentTypeFactoryFunction
                              ) -> Optional[RegisteredArgumentTypeFactoryFunction]:
    return _RegisteredData.argument_type_factories.get(id(function))


def get_argument_type_conversion(function: ArgumentTypeConversionFunction
                                 ) -> Optional[RegisteredArgumentTypeConversionFunction]:
    return _RegisteredData.argument_type_conversions.get(id(function))
