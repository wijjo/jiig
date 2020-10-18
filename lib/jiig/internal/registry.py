"""Task and associated tool data registry."""

from pprint import pformat
from typing import Text, Optional, List, Dict, Set, Iterator, Tuple, Any

from jiig.internal import tool_options, NotesRawData, \
    CommonArgumentsSpecList, CommonArgumentsDestDict, TaskArgumentsSpecList, \
    OptionFlags, ArgumentData, OptionsList, ArgumentsList
from jiig.internal.mapped_task import MappedTask
from jiig.internal.help_formatter import HelpTaskVisibility
from jiig.task_runner import RunnerFactoryFunction, TaskFunction, TaskFunctionsSpec
from jiig.utility.cli import make_dest_name, make_metavar
from jiig.utility.console import abort, log_error
from jiig.utility.footnotes import FootnoteDict
from jiig.utility.general import make_list


# === Registered data


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


def tool(name: Text = None,
         description: Text = None,
         notes: NotesRawData = None,
         disable_alias: bool = None,
         disable_help: bool = None,
         disable_debug: bool = None,
         disable_dry_run: bool = None,
         disable_verbose: bool = None,
         common_arguments: CommonArgumentsSpecList = None,
         common_footnotes: FootnoteDict = None):
    """
    Declare tool options and metadata.

    :param name: name of tool
    :param description: description of tool
    :param notes: additional notes displayed after help body
    :param disable_alias: disable aliases if True
    :param disable_help: disable help task if True
    :param disable_debug: disable debug option if True
    :param disable_dry_run: disable dry run option if True
    :param disable_verbose: disable verbose option if True
    :param common_arguments: options (or arguments) that can be shared between tasks
    :param common_footnotes: common named common_footnotes for reference by options/arguments
    """
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
    if common_arguments is not None:
        arguments: CommonArgumentsSpecList = []
        arguments_by_dest: CommonArgumentsDestDict = {}
        if not isinstance(common_arguments, (tuple, list)):
            abort('Bad common_arguments specification for tool.')
        for argument_data in common_arguments:
            arguments.append(argument_data)
            arguments_by_dest[argument_data['dest']] = argument_data
        tool_options.set_common_arguments(arguments)
        tool_options.set_common_arguments_by_dest_name(arguments_by_dest)
    if common_footnotes is not None:
        tool_options.set_common_footnotes(common_footnotes)


class _MappedTaskDataGenerator:
    def __init__(self, task_function: Optional[TaskFunction]):
        self.task_function = task_function
        self.unsorted_options: List[Tuple[OptionFlags, ArgumentData]] = []
        self.arguments: TaskArgumentsSpecList = []
        self.execution_tasks: List[MappedTask] = []
        self.parent_mapped_task: Optional[MappedTask] = None
        self.footnote_labels: List[Text] = []
        # Data to be finalized before creating the mapped task.
        self.sorted_options: Optional[OptionsList] = None
        self.task_name: Optional[Text] = None
        self.dest_name: Optional[Text] = None
        self.metavar: Optional[Text] = None
        self.help_text: Optional[Text] = None
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

    @staticmethod
    def _is_valid_flag_list(flag_list: Any):
        if not isinstance(flag_list, list):
            return False
        if list(filter(lambda f: not isinstance(f, str), flag_list)):
            return False
        return True

    def merge_arguments_spec_list(
            self, arguments_spec_list: Optional[TaskArgumentsSpecList]):
        if arguments_spec_list:
            for argument_spec in arguments_spec_list:
                error = None
                if isinstance(argument_spec, str):
                    # Simple string: common positional argument dest name.
                    if argument_spec[-1] in ('?', '*', '+'):
                        nargs = argument_spec[-1]
                        dest = argument_spec[:-1]
                    else:
                        nargs = None
                        dest = argument_spec
                    argument_data = tool_options.common_arguments_by_dest_name.get(dest)
                    if argument_data is not None:
                        if nargs is None:
                            self.merge_argument(argument_data)
                        else:
                            self.merge_argument(dict(argument_data, nargs=nargs))
                    else:
                        error = 'Common argument data not found for positional argument.'
                elif isinstance(argument_spec, dict):
                    # Simple dictionary: inline positional argument specification.
                    self.merge_argument(argument_spec)
                elif isinstance(argument_spec, tuple) and len(argument_spec) == 2:
                    # Tuple (pair): (flags, argument spec) for option argument.
                    flag_list, arg_dest_or_data = argument_spec
                    flag_list = make_list(flag_list)
                    if self._is_valid_flag_list(flag_list):
                        if isinstance(arg_dest_or_data, str):
                            dest = arg_dest_or_data
                            # Common argument dest name.
                            argument_data = tool_options.common_arguments_by_dest_name.get(dest)
                            if argument_data is not None:
                                self.merge_option(flag_list, argument_data)
                            else:
                                error = 'Common argument data not found for option.'
                        elif isinstance(arg_dest_or_data, dict):
                            argument_data = arg_dest_or_data
                            self.merge_option(flag_list, argument_data)
                        else:
                            error = 'Option data is not a dictionary.'
                    else:
                        error = f'Option flags ({flag_list}) is not a string list.'
                else:
                    error = 'Argument spec is not a argument string or option pair.'
                if error:
                    log_error('Ignoring bad argument spec:', error,
                              *pformat(argument_spec, compact=True).splitlines())

    def merge_options(self, options_in: OptionsList):
        for flag_list, option_data in options_in:
            self.merge_option(flag_list, option_data)

    def merge_option(self, flag_list: OptionFlags, option_data: ArgumentData):
        option_dest_name = option_data.get('dest', None)
        if option_dest_name:
            if option_dest_name not in self._unique_dest_names:
                self.unsorted_options.append((flag_list, option_data))
                self._unique_dest_names.add(option_dest_name)

    def merge_arguments(self, arguments_in: Optional[ArgumentsList]):
        if arguments_in:
            for argument_data in arguments_in:
                self.merge_argument(argument_data)

    def merge_argument(self, argument_data: ArgumentData):
        argument_dest_name = argument_data.get('dest', None)
        if argument_dest_name:
            if argument_dest_name not in self._unique_dest_names:
                self.arguments.append(argument_data)
                self._unique_dest_names.add(argument_dest_name)

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
                      help_text: Optional[Text],
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

        # Generate the help text.
        self.help_text = help_text.strip() if help_text else ''
        if not self.help_text:
            if self.task_function.__doc__:
                self.help_text = self.task_function.__doc__.strip().splitlines()[0]
            if not self.help_text:
                self.help_text = '(no help in @task decorator or doc string)'

        # Generate the description.
        self.description = description.strip() if description else ''
        if not self.description:
            if self.help_text:
                self.description = f'TASK: {self.help_text}'
            else:
                self.description = '(no description or help in @task decorator or doc string)'

        # Build final options and arguments by merging in ones from related tasks.
        for execution_task in self.execution_tasks:
            if execution_task.options:
                self.merge_options(execution_task.options)
            if execution_task.arguments:
                self.merge_arguments(execution_task.arguments)
        self.sorted_options = sorted(self.unsorted_options, key=lambda o: o[0])

        # Derive the help visibility from the auxiliary and hidden flags
        if hidden_task:
            self.help_visibility = 2
        elif auxiliary_task:
            self.help_visibility = 1


# noinspection PyShadowingBuiltins
def register_task(task_function: TaskFunction,
                  name: Text = None,
                  parent: TaskFunction = None,
                  help: Text = None,
                  description: Text = None,
                  arguments: TaskArgumentsSpecList = None,
                  dependencies: TaskFunctionsSpec = None,
                  receive_trailing_arguments: bool = False,
                  notes: NotesRawData = None,
                  footnotes: FootnoteDict = None,
                  hidden_task: bool = False,
                  auxiliary_task: bool = False):

    # Merge and generate all the data needed for creating a mapped task.
    mt_data = _MappedTaskDataGenerator(task_function)
    mt_data.merge_arguments_spec_list(arguments)
    mt_data.merge_parent(parent)
    mt_data.merge_dependencies(dependencies)
    mt_data.finalize_data(name, help, description, hidden_task, auxiliary_task)

    # Create new mapped task using input and prepared data.
    mapped_task = MappedTask(task_function=task_function,
                             name=mt_data.task_name,
                             parent=mt_data.parent_mapped_task,
                             dest_name=mt_data.dest_name,
                             metavar=mt_data.metavar,
                             help=mt_data.help_text,
                             description=mt_data.description,
                             options=mt_data.sorted_options,
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
