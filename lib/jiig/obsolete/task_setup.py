"""
Initialize runtime task hierarchy.
"""

import re
from inspect import isfunction, signature
from typing import Text, Any, List, Optional

from jiig import config, const, model
from jiig.arg import Choices, Default
from jiig.typing import OptionFlag, ArgumentAdapter, Cardinality
from jiig.util.console import abort

# noinspection RegExpRedundantEscape
ARGUMENT_NAME_REGEX = re.compile(r'^([a-zA-Z][a-zA-Z0-9\-_]*)((?:\[(?:\d+|\*|\+)\])|!|\?)?$')


class _TaskDataArgumentBuilder:
    """
     Used by TaskDataBuilder to populate arguments and options.

     Error list is held by calling task builder.
     """

    def __init__(self, errors: List[Text], error_preamble):
        self.error_preamble = error_preamble
        self.opts: List[model.OptionData] = []
        self.args: List[model.ArgumentData] = []
        self.errors = errors

    def _error(self, message: Text):
        self.errors.append(f'{self.error_preamble}: {message}')

    def add(self, name: Text, data: Any):
        flags: Optional[List[OptionFlag]] = None
        descriptions: List[Text] = []
        adapters: Optional[List[ArgumentAdapter]] = None
        cardinality: Optional[Cardinality] = None
        default_value: Optional[Any] = None
        choices: Optional[List] = None
        parsed_name = ARGUMENT_NAME_REGEX.match(name)
        is_boolean = False
        if not parsed_name:
            self._error(f'Bad argument name.')
            return
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
                        self._error(f'Adapter function {item.__name__} missing value parameter.')
                    else:
                        adapters.append(item)
                elif isinstance(item, Choices):
                    choices = list(item.values)
                elif isinstance(item, Default):
                    default_value = item.value
                else:
                    self._error(f'Bad argument tuple item (#{item_idx + 1}): {item}')
                    return
        if len(descriptions) == 0:
            description = '(no description)'
        else:
            if len(descriptions) > 1:
                self._error('Too many description strings for argument.')
            description = descriptions[-1]
        if flags is not None:
            self.opts.append(model.OptionData(arg_name,
                                              flags,
                                              description,
                                              adapters=adapters,
                                              cardinality=cardinality,
                                              default_value=default_value,
                                              choices=choices,
                                              is_boolean=is_boolean))
        else:
            if is_boolean:
                self._error(f'Ignoring "!" modifier for positional argument.')
            self.args.append(model.ArgumentData(arg_name,
                                                description,
                                                adapters=adapters,
                                                cardinality=cardinality,
                                                default_value=default_value,
                                                choices=choices))


class _TaskDataBuilder:
    """Build TaskData hierarchy and keep track of errors."""

    def __init__(self):
        self.errors: List[Text] = []

    def build_tool_tasks(self,
                         tool_config: config.Tool,
                         ) -> Optional[model.TaskRuntime]:
        return self.build_task(tool_config.root_task, '(root)', 2)

    def resolve_config_task(self, task_spec: Any) -> Optional[config.Task]:
        if isinstance(task_spec, config.Task):
            return task_spec
        # Assume it's a module - look for the specially-named global.
        task_global = getattr(task_spec, const.TASK_MODULE_GLOBAL_NAME, None)
        if isinstance(task_global, config.Task):
            return task_global
        self.errors.append(f'Task specification is not a Task object or module: {task_spec}')
        return None

    def build_task(self,
                   task_spec: Any,
                   name: Text,
                   visibility: int,
                   ) -> Optional[model.TaskRuntime]:
        config_task = self.resolve_config_task(task_spec)
        if config_task is None:
            return None
        task_class = config_task.__class__
        arg_error_preamble = f'{task_class.__module__}.{task_class.__name__}[{name}]'
        arg_builder = _TaskDataArgumentBuilder(self.errors, arg_error_preamble)
        for arg_name, arg_obj in config_task.args.items():
            arg_builder.add(arg_name, arg_obj)
        sub_tasks: List[model.TaskRuntime] = []
        for sub_visibility, spec_dict in ((0, config_task.tasks),
                                          (1, config_task.secondary_tasks),
                                          (2, config_task.hidden_tasks)):
            for sub_task_name, sub_task_spec in spec_dict.items():
                sub_task = self.build_task(sub_task_spec, sub_task_name, sub_visibility)
                if sub_task is not None:
                    sub_tasks.append(sub_task)
        return model.TaskRuntime(
            name=name,
            visibility=visibility,
            opts=arg_builder.opts,
            args=arg_builder.args,
            sub_tasks=sub_tasks,
            receive_trailing_arguments=config_task.receive_trailing_arguments,
            run_functions=config_task.run_functions,
            done_functions=config_task.done_functions,
        )


def initialize(tool_config: config.Tool) -> model.TaskRuntime:
    """
    Initialize/populate task hierarchy starting from Tool configuration.

    :param tool_config: tool configuration
    :return: task runtime data
    """
    task_builder = _TaskDataBuilder()
    root_task = task_builder.build_tool_tasks(tool_config)
    if root_task is None or task_builder.errors:
        abort('Failed to build task hierarchy.', task_builder.errors)
    return root_task
