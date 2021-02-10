"""
Task registry.

Provides on-demand access to TaskData objects based on Tool/Task configuration.
"""

from typing import Text, List, Optional, Any, Union

from jiig import config, const
from jiig.util.console import log_error, abort
from jiig.util.general import binary_search

from jiig.obsolete.task_runtime import TaskRuntime


def resolve_config_task(task_spec: Any) -> Optional[config.Task]:
    """
    Resolve task spec to config Task.

    :param task_spec: task specification, i.e. Task object or module
    :return: config Task if it it is a proper Task or task module, or None if not
    """
    if isinstance(task_spec, config.Task):
        return task_spec
    # Assume it's a module - look for the specially-named global.
    task_global = getattr(task_spec, const.TASK_MODULE_GLOBAL_NAME, None)
    if isinstance(task_global, config.Task):
        return task_global
    log_error(f'Task specification is not a Task object or module.', task_spec)
    return None


def find_config_sub_task(config_task: config.Task, name: Text) -> Optional[config.Task]:
    """
    Find a config sub-task by name.

    :param config_task: parent config task
    :param name: name to find
    :return: config sub-task if found or None if not
    """
    task_spec = (config_task.tasks.get(name)
                 or config_task.secondary_tasks.get(name)
                 or config_task.hidden_tasks.get(name))
    if task_spec is None:
        return None
    return resolve_config_task(task_spec)


class TaskRegistry:
    """
    Task registry with cached access to TaskData items.

    This facility attempts to delay as much of the performance penalty, given
    that most task implements only require access to a single task or a very
    limited subset.
    """

    def __init__(self, config_tool: config.Tool):
        self.root_config_task = resolve_config_task(config_tool.root_task)
        if self.root_config_task is None:
            abort(f'Failed to resolve root task based on task specification.',
                  config_tool.root_task)
        # The cache first saves the resolved config task, which morphs into the
        # runtime task data, when actually required.
        self.task_cache: List[Union[config.Task, TaskRuntime]] = []

    def get_task(self, name: Text) -> Optional[TaskRuntime]:
        """
        Look up cached TaskData by name.

        The cache strategy captures all tasks resolved while descending the config hierarchy.

        :param name: full task name
        :return: TaskData object or None if not found
        """
        return self._get_task(self.root_config_task, self.task_cache, name)

    @staticmethod
    def _get_task(config_task: config.Task,
                  task_list: List[TaskRuntime],
                  name: Text,
                  ) -> Optional[TaskRuntime]:
        task_name, sub_name = name.split(const.FULL_NAME_SEPARATOR, maxsplit=1)
        task = binary_search(task_list, task_name, key=lambda t: t.name)
        # No cached config.Task or TaskData yet?
        if task is None:
            # Start by caching the config task, if it is a valid task spec.
            config_task = find_config_sub_task(config_task, name)
            if config_task is None:
                # No good.
                return None



        if name in self.tasks_by_name:
            return self.tasks_by_name[name]
        name_parts = name.split(const.FULL_NAME_SEPARATOR)
        config_task = self.config_tool.root_task
        for name_part in name_parts:
            if name_part not in config_task.
