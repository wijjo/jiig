"""Task and associated tool data registry."""
from typing import Text, Optional, List, Dict, Set, Iterator, Sequence

from jiig.internal import tool_options, \
    ArgumentList, OptionDict, OptionRawDict, OptionDestFlagsDict, \
    TaskFunction, RunnerFactoryFunction
from jiig.internal.mapped_task import MappedTask
from jiig.utility.cli import make_dest_name, make_metavar
from jiig.utility.console import abort, log_error
from jiig.utility.general import make_tuple

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
        if not mt.parent and mt.name:
            if include_hidden or mt.name not in _RegisteredData.hidden_task_names:
                yield mt


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
        tool_options.set_name(name)
    if description is not None:
        tool_options.set_description(description)
    if epilog is not None:
        tool_options.set_epilog(epilog)
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
    if common_options is not None:
        options: OptionDict = {}
        flags_by_dest: OptionDestFlagsDict = {}
        for raw_flags, option_data in common_options.items():
            flag_tuple = make_tuple(raw_flags)
            options[flag_tuple] = option_data
            flags_by_dest[option_data['dest']] = flag_tuple
        tool_options.set_common_options(options)
        tool_options.set_common_flags_by_dest(flags_by_dest)


class _MappedTaskDataGenerator:
    def __init__(self, task_function: Optional[TaskFunction]):
        self.task_function = task_function
        self.options: OptionDict = {}
        self.arguments: ArgumentList = []
        self.execution_tasks: List[MappedTask] = []
        self.parent_mapped_task: Optional[MappedTask] = None
        # Data to be finalized before creating the mapped task.
        self.task_name: Optional[Text] = None
        self.dest_name: Optional[Text] = None
        self.metavar: Optional[Text] = None
        self.help_text: Optional[Text] = None
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
            abort(f'Unmapped task for function: {task_function.__name__}()')
        if not mapped_task.name:
            abort(f'Mapped task {mapped_task.__class__.__name__} has no name')
        return mapped_task

    def merge_raw_options(self, raw_options_in: Optional[OptionRawDict]):
        if raw_options_in:
            for raw_flags, option_data in raw_options_in.items():
                flag_tuple = make_tuple(raw_flags)
                self.options[flag_tuple] = option_data

    def merge_common_options(self, common_options_in: Optional[Sequence[Text]]):
        if common_options_in:
            for dest in common_options_in:
                flag_tuple = tool_options.common_flags_by_dest.get(dest)
                if flag_tuple is not None:
                    option_data = tool_options.common_options[flag_tuple]
                    self.options[flag_tuple] = option_data
                else:
                    log_error(f'Ignoring unknown common option "{dest}".')

    def merge_common_arguments(self, common_arguments_in: Optional[Sequence[Text]]):
        if common_arguments_in:
            for option_spec in common_arguments_in:
                if option_spec[-1] in ('?', '*', '+'):
                    nargs = option_spec[-1]
                    dest = option_spec[:-1]
                else:
                    nargs = None
                    dest = option_spec
                flag_tuple = tool_options.common_flags_by_dest.get(dest)
                if flag_tuple is not None:
                    option_data = tool_options.common_options[flag_tuple]
                    if nargs is None:
                        self.arguments.append(option_data)
                    else:
                        self.arguments.append(dict(option_data, nargs=nargs))
                else:
                    log_error(f'Ignoring unknown common argument "{dest}".')

    def merge_options(self, options_in: OptionDict):
        for flag_tuple, option_data in options_in.items():
            option_dest_name = option_data.get('dest', None)
            if option_dest_name:
                if option_dest_name not in self._unique_dest_names:
                    self.options[flag_tuple] = option_data
                    self._unique_dest_names.add(option_dest_name)

    def merge_arguments(self, arguments_in: Optional[ArgumentList]):
        if arguments_in:
            for argument_data in arguments_in:
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

    def generate_names(self, name: Optional[Text]):
        if name:
            self.task_name = name
        else:
            if self.task_function.__name__.startswith('_'):
                abort(f'Private @task function "{self.task_function.__name__}()"'
                      f' has no name attribute.')
            self.task_name = self.task_function.__name__
        names = []
        container_mapped_task = self.parent_mapped_task
        while container_mapped_task:
            names.append(container_mapped_task.name.upper())
            container_mapped_task = container_mapped_task.parent
        names.append(self.task_name.upper())
        self.dest_name = make_dest_name(*names)
        self.metavar = make_metavar(*names)

    def generate_help_text(self, help_text: Optional[Text]):
        if help_text:
            self.help_text = help_text
        else:
            if self.task_function.__doc__:
                doc_string = self.task_function.__doc__.strip()
                if doc_string:
                    self.help_text = doc_string.splitlines()[0]
            if not self.help_text:
                self.help_text = '(no help in @task decorator or doc string)'

    def finalize(self):
        for execution_task in self.execution_tasks:
            if execution_task.options:
                self.merge_options(execution_task.options)
            if execution_task.arguments:
                self.merge_arguments(execution_task.arguments)
        self.options = dict(sorted(list(self.options.items()), key=lambda o: o[0]))


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

    # Merge and generate all the data needed for creating a mapped task.
    mt_data = _MappedTaskDataGenerator(task_function)
    mt_data.merge_raw_options(options)
    mt_data.merge_common_options(common_options)
    mt_data.merge_arguments(arguments)
    mt_data.merge_common_arguments(common_arguments)
    mt_data.merge_parent(parent)
    mt_data.merge_dependencies(dependencies)
    mt_data.generate_names(name)
    mt_data.generate_help_text(help)
    mt_data.finalize()

    # Create new mapped task using input and prepared data.
    mapped_task = MappedTask(task_function=task_function,
                             name=mt_data.task_name,
                             parent=mt_data.parent_mapped_task,
                             dest_name=mt_data.dest_name,
                             metavar=mt_data.metavar,
                             help=mt_data.help_text,
                             epilog=epilog,
                             options=mt_data.options,
                             arguments=mt_data.arguments,
                             trailing_arguments=trailing_arguments,
                             need_trailing_arguments=trailing_arguments,
                             execution_tasks=mt_data.execution_tasks,
                             hidden_task=hidden_task,
                             auxiliary_task=auxiliary_task)

    # Copy the trailing arguments flag to the top level task
    if trailing_arguments:
        container_mapped_task = mapped_task.parent
        while container_mapped_task:
            if not container_mapped_task.parent:
                container_mapped_task.need_trailing_arguments = True
            container_mapped_task = container_mapped_task.parent

    # Register new MappedTask into global data structures.
    _RegisteredData.mapped_tasks_by_id[id(mapped_task.task_function)] = mapped_task
    if mapped_task.dest_name:
        _RegisteredData.mapped_tasks_by_dest_name[mapped_task.dest_name] = mapped_task
    if mapped_task.hidden_task:
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
