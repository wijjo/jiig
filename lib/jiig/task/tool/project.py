"""
Tool project creation task.
"""

import os
from typing import Text, Optional

import jiig
from jiig.util.template_expansion import expand_folder


DEFAULT_TASK_NAME = 'generated_task'


TASK = jiig.Task(
    description='Create Jiig tool project.',
    args={
        'FORCE[!]': ('-f', '--force', 'Force overwriting of target files.'),
        'TOOL_NAME': ('-T', '--tool-name', 'Tool name (default: <folder name>).'),
        'TASK_NAME': ('-t', '--task-name', f'Task name (default: "{DEFAULT_TASK_NAME}").',
                      jiig.arg.default(DEFAULT_TASK_NAME)),
        'TOOL_FOLDER[?]': ('Generated tool output folder.',
                           jiig.arg.path_is_folder,
                           jiig.arg.path_to_absolute,
                           jiig.arg.default('.')),
    },
)


# For type inspection only.
class Data:
    FORCE: bool
    TOOL_NAME: Text
    TASK_NAME: Text
    TOOL_FOLDER: Optional[Text]


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    expand_folder(
        os.path.join(runner.tool.jiig_root_folder,
                     jiig.const.TOOL_TEMPLATES_FOLDER,
                     'project'),
        data.TOOL_FOLDER,
        overwrite=data.FORCE,
        symbols={
            'template_tool_name': (data.TOOL_NAME
                                   or os.path.basename(data.TOOL_FOLDER)),
            'template_task_name': data.TASK_NAME,
        },
    )
