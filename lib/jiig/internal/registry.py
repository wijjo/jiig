"""Task and associated tool data registry."""

from typing import Dict, Text, Optional, Callable, List, Iterator, Sequence, Set

from jiig.internal.mapped_task import MappedTask, TaskFunction, \
    OptionDict, ArgumentList, OptionDestFlagsDict, OptionRawDict
from jiig.task_runner import RunnerData, TaskRunner
from jiig.utility.cli import make_dest_name, make_metavar
from jiig.utility.console import abort, log_error
from jiig.utility.general import make_tuple


# === Types

RunnerFactoryFunction = Callable[[RunnerData], TaskRunner]

# === Runner factory

# Runner factory registered by @runner_factory decorator. Last registered one wins.
RUNNER_FACTORY: Optional[RunnerFactoryFunction] = None


# === Task registry


MAPPED_TASKS: List[MappedTask] = []
# For quick lookups of parent and dependency tasks while processing @task decorator calls.
MAPPED_TASKS_BY_ID: Dict[int, MappedTask] = {}
# To help map task name in command line arguments to MappedTask by argparse destination names.
MAPPED_TASKS_BY_DEST_NAME: Dict[Text, MappedTask] = {}
# Names of tasks that are listed separately from tool tasks.
AUXILIARY_TASK_NAMES: Set[Text] = set()
# Names of tasks that are only shown when the ALL_TASKS option is used for help.
HIDDEN_TASK_NAMES: Set[Text] = set()


def get_tool_tasks(include_hidden: bool = False) -> Iterator[MappedTask]:
    """
    Yield primary tasks (unsorted).

    :param include_hidden: include hidden task names if True
    :return: iterable MappedTask objects
    """
    for mt in MAPPED_TASKS:
        if not mt.parent and mt.name:
            if include_hidden or mt.name not in HIDDEN_TASK_NAMES:
                yield mt


# === Options

class ToolOptions:
    name = None
    description = None
    epilog = None
    disable_alias = False
    disable_help = False
    disable_debug = False
    disable_dry_run = False
    disable_verbose = False
    common_arguments: ArgumentList = None
    common_options: OptionDict = {}
    common_flags_by_dest: OptionDestFlagsDict = {}


def tool(name: Text = None,
         description: Text = None,
         epilog: Text = None,
         disable_alias: bool = None,
         disable_help: bool = None,
         disable_debug: bool = None,
         disable_dry_run: bool = None,
         disable_verbose: bool = None,
         common_options: OptionRawDict = None):
    """
    Declare tool options and metadata.

    :param name: name of tool
    :param description: description of tool
    :param epilog: additional help text displayed at the bottom
    :param disable_alias: disable aliases if True
    :param disable_help: disable help task if True
    :param disable_debug: disable debug option if True
    :param disable_dry_run: disable dry run option if True
    :param disable_verbose: disable verbose option if True
    :param common_options: options (or arguments) that can be shared between tasks
    """
    # Only set values for the keywords that were provided.
    if name is not None:
        ToolOptions.name = name
    if description is not None:
        ToolOptions.description = description
    if epilog is not None:
        ToolOptions.epilog = epilog
    if disable_alias is not None:
        ToolOptions.disable_alias = disable_alias
    if disable_help is not None:
        ToolOptions.disable_help = disable_help
    if disable_debug is not None:
        ToolOptions.disable_debug = disable_debug
    if disable_dry_run is not None:
        ToolOptions.disable_dry_run = disable_dry_run
    if disable_verbose is not None:
        ToolOptions.disable_verbose = disable_verbose
    if common_options is not None:
        for raw_flags, option_data in common_options.items():
            flag_tuple = make_tuple(raw_flags)
            ToolOptions.common_options[flag_tuple] = option_data
            ToolOptions.common_flags_by_dest[option_data['dest']] = flag_tuple


class OptionArgumentPreparer:

    def __init__(self, task_function: TaskFunction):
        self.task_function = task_function
        self.arguments: ArgumentList = []
        self.parent_mapped_task = None
        self.unsorted_options: OptionDict = {}
        self.execution_tasks: List[MappedTask] = []
        self.unique_dest_names: Set[Text] = set()
        self.unique_function_ids: Set[int] = set()
        self.trailing_arguments = False
        self.finalized = False
        self.name: Optional[Text] = None
        self.help_text: Optional[Text] = None
        self.epilog: Optional[Text] = None
        self.dest_name: Optional[Text] = None
        self.metavar: Optional[Text] = None
        self.hidden_task = False
        self.auxiliary_task = False
        self.sorted_options: Optional[OptionDict] = None

    def merge_raw_options(self, raw_options: OptionRawDict):
        for raw_flags, option_data in raw_options.items():
            flag_tuple = make_tuple(raw_flags)
            self.unsorted_options[flag_tuple] = option_data

    def merge_common_options(self, common_options: Sequence[Text]):
        for dest in common_options:
            flag_tuple = ToolOptions.common_flags_by_dest.get(dest)
            if flag_tuple is not None:
                option_data = ToolOptions.common_options[flag_tuple]
                self.unsorted_options[flag_tuple] = option_data
            else:
                log_error(f'Ignoring unknown common option "{dest}".')

    def merge_common_arguments(self, common_arguments: Sequence[Text]):
        for option_spec in common_arguments:
            if option_spec[-1] in ('?', '*', '+'):
                nargs = option_spec[-1]
                dest = option_spec[:-1]
            else:
                nargs = None
                dest = option_spec
            flag_tuple = ToolOptions.common_flags_by_dest.get(dest)
            if flag_tuple is not None:
                option_data = ToolOptions.common_options[flag_tuple]
                if nargs is None:
                    self.arguments.append(option_data)
                else:
                    self.arguments.append(dict(option_data, nargs=nargs))
            else:
                log_error(f'Ignoring unknown common argument "{dest}".')

    def merge_options(self, options: OptionDict):
        for flag_tuple, option_data in options.items():
            option_dest_name = option_data.get('dest', None)
            if option_dest_name:
                if option_dest_name not in self.unique_dest_names:
                    self.unsorted_options[flag_tuple] = option_data
                    self.unique_dest_names.add(option_dest_name)

    def merge_arguments(self, arguments: ArgumentList):
        for argument_data in arguments:
            argument_dest_name = argument_data.get('dest', None)
            if argument_dest_name:
                if argument_dest_name not in self.unique_dest_names:
                    self.arguments.append(argument_data)
                    self.unique_dest_names.add(argument_dest_name)

    def merge_parent(self, parent: TaskFunction):
        self.parent_mapped_task = MAPPED_TASKS_BY_ID.get(id(parent))
        if not self.parent_mapped_task:
            abort(f'Unmapped parent task: {parent.__name__}')
        if not self.parent_mapped_task.name:
            abort(f'Parent task {self.parent_mapped_task.__class__.__name__}'
                  f' does not have a name')
        if self.parent_mapped_task.execution_tasks:
            for parent_execution_task in self.parent_mapped_task.execution_tasks:
                self.execution_tasks.append(parent_execution_task)
                self.unique_function_ids.add(id(parent_execution_task.task_function))
        self.execution_tasks.append(self.parent_mapped_task)
        self.unique_function_ids.add(id(self.parent_mapped_task.task_function))

    def merge_dependencies(self, dependencies: List[TaskFunction]):
        # Recursion is not needed since related tasks were already rolled up.
        for dependency_function in dependencies:
            dependency_function_id = id(dependency_function)
            if dependency_function_id in self.unique_function_ids:
                continue
            dependency_mapped_task = MAPPED_TASKS_BY_ID.get(dependency_function_id, None)
            if not dependency_mapped_task:
                continue
            # Execution tasks property yields child tasks and the parent task.
            for dependency_execution_task in dependency_mapped_task.execution_tasks:
                dependency_execution_function_id = id(dependency_execution_task.task_function)
                if dependency_execution_function_id in self.unique_function_ids:
                    continue
                self.execution_tasks.append(dependency_execution_task)
                self.unique_function_ids.add(dependency_execution_function_id)
            self.execution_tasks.append(dependency_mapped_task)
            self.unique_function_ids.add(dependency_function_id)

    def set_name(self, name: Text):
        self.name = name

    def set_help(self, help_text: Text):
        self.help_text = help_text

    def set_epilog(self, epilog: Text):
        self.epilog = epilog

    def set_trailing_arguments(self, trailing_arguments: bool):
        self.trailing_arguments = trailing_arguments

    def set_hidden_task(self, hidden_task: bool):
        self.hidden_task = hidden_task

    def set_auxiliary_task(self, auxiliary_task: bool):
        self.auxiliary_task = auxiliary_task

    def create_mapped_task(self) -> MappedTask:
        if not self.finalized:
            self._finalize_related_tasks()
            self._finalize_names()
            self._finalize_help()
            self._finalize_trailing_arguments()
            self._finalize_options()
            self.finalized = True
        return MappedTask(task_function=self.task_function,
                          name=self.name,
                          parent=self.parent_mapped_task,
                          dest_name=self.dest_name,
                          metavar=self.metavar,
                          help=self.help_text,
                          epilog=self.epilog,
                          options=self.sorted_options,
                          arguments=self.arguments,
                          trailing_arguments=self.trailing_arguments,
                          need_trailing_arguments=self.trailing_arguments,
                          execution_tasks=self.execution_tasks,
                          hidden_task=self.hidden_task,
                          auxiliary_task=self.auxiliary_task)

    def _finalize_names(self):
        if not self.name:
            if self.task_function.__name__.startswith('_'):
                abort(f'Private @task function "{self.task_function.__name__}()"'
                      f' has no name attribute.')
            self.name = self.task_function.__name__
        names = []
        ancestor_mapped_task = self.parent_mapped_task
        while ancestor_mapped_task:
            names.append(ancestor_mapped_task.name.upper())
            ancestor_mapped_task = ancestor_mapped_task.parent
        names.append(self.name.upper())
        self.dest_name = make_dest_name(*names)
        self.metavar = make_metavar(*names)

    def _finalize_related_tasks(self):
        for execution_task in self.execution_tasks:
            if execution_task.options:
                self.merge_options(execution_task.options)
            if execution_task.arguments:
                self.merge_arguments(execution_task.arguments)

    def _finalize_help(self):
        if not self.help_text:
            if self.task_function.__doc__:
                doc_string = self.task_function.__doc__.strip()
                if doc_string:
                    self.help_text = doc_string.splitlines()[0]
            if not self.help_text:
                self.help_text = '(no help in @task decorator or doc string)'

    def _finalize_trailing_arguments(self):
        if self.trailing_arguments and self.parent_mapped_task:
            parent_mapped_task = self.parent_mapped_task
            while True:
                if not parent_mapped_task.parent:
                    parent_mapped_task.need_trailing_arguments = True
                    break
                parent_mapped_task = parent_mapped_task.parent

    def _finalize_options(self):
        option_pairs = [
            (o_flags, o_data)
            for o_flags, o_data in self.unsorted_options.items()
        ]
        self.sorted_options = dict(sorted(option_pairs, key=lambda o: o[0]))


# noinspection PyShadowingBuiltins
def register_task(task_function: TaskFunction,
                  name: Text = None,
                  parent: TaskFunction = None,
                  help: Text = None,
                  epilog: Text = None,
                  options: OptionRawDict = None,
                  arguments: ArgumentList = None,
                  dependencies: List[TaskFunction] = None,
                  trailing_arguments: bool = False,
                  common_options: Sequence[Text] = None,
                  common_arguments: Sequence[Text] = None,
                  hidden_task: bool = False,
                  auxiliary_task: bool = False):
    # Prepare data for the mapped task.
    preparer = OptionArgumentPreparer(task_function)
    if name:
        preparer.set_name(name)
    if help:
        preparer.set_help(help)
    if epilog:
        preparer.set_epilog(epilog)
    if trailing_arguments:
        preparer.set_trailing_arguments(trailing_arguments)
    if options:
        preparer.merge_raw_options(options)
    if common_options:
        preparer.merge_common_options(common_options)
    if arguments:
        preparer.merge_arguments(arguments)
    if common_arguments:
        preparer.merge_common_arguments(common_arguments)
    if parent:
        preparer.merge_parent(parent)
    if dependencies:
        preparer.merge_dependencies(dependencies)
    if hidden_task:
        preparer.set_hidden_task(True)
    if auxiliary_task:
        preparer.set_auxiliary_task(True)

    # Create the new mapped task.
    mapped_task = preparer.create_mapped_task()

    # Complete the registration, now that there is a new MappedTask.
    MAPPED_TASKS_BY_ID[id(task_function)] = mapped_task
    if preparer.dest_name:
        MAPPED_TASKS_BY_DEST_NAME[preparer.dest_name] = mapped_task
    if hidden_task:
        HIDDEN_TASK_NAMES.add(name)
    if auxiliary_task:
        AUXILIARY_TASK_NAMES.add(name)

    # Add to sub_tasks list of parent, if there is a parent.
    if preparer.parent_mapped_task:
        if preparer.parent_mapped_task.sub_tasks is None:
            preparer.parent_mapped_task.sub_tasks = []
        preparer.parent_mapped_task.sub_tasks.append(mapped_task)
    else:
        MAPPED_TASKS.append(mapped_task)
