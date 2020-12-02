"""Task and associated tool data registry."""

from typing import Text, Optional, List, Set, Sequence, Dict, Type

from jiig.utility.help_formatter import HelpTaskVisibility
from jiig.utility.console import abort
from jiig.utility.footnotes import NoteDict, NotesSpec
from jiig.utility.general import make_list

from . import data, options


def register_tool(name: Text = None,
                  description: Text = None,
                  disable_alias: bool = None,
                  disable_help: bool = None,
                  disable_debug: bool = None,
                  disable_dry_run: bool = None,
                  disable_verbose: bool = None,
                  expose_hidden_tasks: bool = None,
                  notes: NotesSpec = None,
                  footnotes: NoteDict = None,
                  runner_cls: Type[data.RegisteredRunner] = None,
                  ):
    data.REGISTERED_TOOL = data.RegisteredTool(
        name=name,
        description=description,
        disable_alias=disable_alias or False,
        disable_help=disable_help or False,
        disable_debug=disable_debug or False,
        disable_dry_run=disable_dry_run or False,
        disable_verbose=disable_verbose or False,
        expose_hidden_tasks=expose_hidden_tasks or False,
        notes=make_list(notes),
        footnotes=footnotes or {},
        runner_cls=runner_cls,
    )


class _RegisteredTaskFinalizer:
    def __init__(self,
                 task_function: Optional[data.TaskFunction],
                 arguments: Sequence[data.Argument]):
        self.task_function = task_function
        self.arguments = list(arguments)
        self.execution_tasks: List[data.RegisteredTask] = []
        self.parent_task: Optional[data.RegisteredTask] = None
        self.footnote_labels: List[Text] = []
        # Data to be finalized before creating the registered task.
        self.task_name: Optional[Text] = None
        self.task_full_name: Optional[Text] = None
        self.description: Optional[Text] = None
        self.help_visibility = HelpTaskVisibility.NORMAL
        # Data used during merge processing.
        self._unique_argument_names: Set[Text] = set()
        self._unique_function_ids: Set[int] = set()

    @staticmethod
    def get_task(task_function: Optional[data.TaskFunction]) -> Optional[data.RegisteredTask]:
        if not task_function:
            return None
        task = data.REGISTERED_TASKS_BY_ID.get(id(task_function))
        if not task:
            abort('No registered task for function:', f'{task_function.__name__}()')
        return task

    class ArgumentMergeError(Exception):
        pass

    def merge_parent(self, parent_task_function: data.TaskFunction):
        self.parent_task = self.get_task(parent_task_function)
        if self.parent_task:
            if self.parent_task.execution_tasks:
                for parent_execution_task in self.parent_task.execution_tasks:
                    self.execution_tasks.append(parent_execution_task)
                    self._unique_function_ids.add(id(parent_execution_task.task_function))
            self.execution_tasks.append(self.parent_task)
            self._unique_function_ids.add(id(self.parent_task.task_function))

    def merge_dependencies(self, dependencies: Optional[List[data.TaskFunction]]):
        if dependencies:
            # Recursion is not needed since related tasks were already rolled up.
            for dependency_function in dependencies:
                dependency_function_id = id(dependency_function)
                if dependency_function_id in self._unique_function_ids:
                    continue
                dependency_registered_task = data.REGISTERED_TASKS_BY_ID.get(
                    dependency_function_id, None)
                if not dependency_registered_task:
                    continue
                # Execution tasks property yields child tasks and the parent task.
                for dependency_execution_task in dependency_registered_task.execution_tasks:
                    dependency_execution_function_id = id(dependency_execution_task.task_function)
                    if dependency_execution_function_id in self._unique_function_ids:
                        continue
                    self.execution_tasks.append(dependency_execution_task)
                    self._unique_function_ids.add(dependency_execution_function_id)
                self.execution_tasks.append(dependency_registered_task)
                self._unique_function_ids.add(dependency_function_id)

    def finalize_data(self,
                      name: Optional[Text],
                      description: Optional[Text],
                      hidden_task: Optional[bool],
                      auxiliary_task: Optional[bool]):

        # The name defaults to the task function name.
        if name:
            self.task_name = name
        else:
            if self.task_function.__name__.startswith('_'):
                abort(f'Private @task function "{self.task_function.__name__}()"'
                      f' has no name attribute.')
            self.task_name = self.task_function.__name__

        # Derive the task full name.
        if self.parent_task:
            self.task_full_name = options.FULL_NAME_SEPARATOR.join(
                [self.parent_task.full_name, self.task_name])
        else:
            self.task_full_name = self.task_name

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
                        if argument.name not in self._unique_argument_names:
                            self.arguments.append(argument)
                            self._unique_argument_names.add(argument.name)

        # Derive the help visibility from the auxiliary and hidden flags
        if hidden_task:
            self.help_visibility = HelpTaskVisibility.HIDDEN
        elif auxiliary_task:
            self.help_visibility = HelpTaskVisibility.AUXILIARY


def register_task(task_function: data.TaskFunction,
                  name: data.ArgName = None,
                  parent: data.TaskFunction = None,
                  description: data.Description = None,
                  arguments: Sequence[data.Argument] = None,
                  dependencies: data.TaskFunctionsSpec = None,
                  receive_trailing_arguments: bool = False,
                  notes: NotesSpec = None,
                  footnotes: NoteDict = None,
                  hidden_task: bool = False,
                  auxiliary_task: bool = False):

    # Merge and generate all the data needed for creating a registered task.
    finalized_data = _RegisteredTaskFinalizer(task_function, arguments)
    finalized_data.merge_parent(parent)
    finalized_data.merge_dependencies(dependencies)
    finalized_data.finalize_data(name, description, hidden_task, auxiliary_task)

    # Create new registered task using input and prepared data.
    registered_task = data.RegisteredTask(
        task_function=task_function,
        name=finalized_data.task_name,
        full_name=finalized_data.task_full_name,
        parent=finalized_data.parent_task,
        description=finalized_data.description,
        arguments=finalized_data.arguments,
        notes=make_list(notes),
        footnotes=footnotes,
        receive_trailing_arguments=receive_trailing_arguments,
        execution_tasks=finalized_data.execution_tasks,
        help_visibility=finalized_data.help_visibility)

    # Cascade trailing arguments flag upwards to signal need for capture.
    if receive_trailing_arguments:
        stack_registered_task = registered_task
        while stack_registered_task:
            stack_registered_task.capture_trailing_arguments = True
            stack_registered_task = stack_registered_task.parent

    # Register new RegisteredTask into global data structures.
    data.REGISTERED_TASKS_BY_ID[id(registered_task.task_function)] = registered_task
    data.REGISTERED_TASKS_BY_NAME[registered_task.full_name] = registered_task

    # Attach to parent sub-tasks or register globally if there is no parent.
    if registered_task.parent:
        if registered_task.parent.sub_tasks is None:
            registered_task.parent.sub_tasks = []
        registered_task.parent.sub_tasks.append(registered_task)
    else:
        data.REGISTERED_TASKS.append(registered_task)
    return registered_task


def get_sorted_tasks() -> List[data.RegisteredTask]:
    if data.REGISTERED_TASKS_SORTED is None:
        data.REGISTERED_TASKS_SORTED = sorted(data.REGISTERED_TASKS, key=lambda m: m.name)
    return data.REGISTERED_TASKS_SORTED


def get_task_by_name(name: Text) -> Optional[data.RegisteredTask]:
    return data.REGISTERED_TASKS_BY_NAME.get(name)


def get_tasks_by_name() -> Dict[Text, data.RegisteredTask]:
    return data.REGISTERED_TASKS_BY_NAME


def get_tool() -> data.RegisteredTool:
    """
    Get registered tool.

    :return: registered tool data
    """
    if not data.REGISTERED_TOOL:
        abort('No tool has been registered.')
    return data.REGISTERED_TOOL
