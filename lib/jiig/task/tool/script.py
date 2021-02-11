"""Tool creation task."""

import os
from typing import Text, Optional

import jiig
from jiig.util.template_expansion import expand_folder


TASK = jiig.Task(
    description='Create monolithic Jiig tool script.',
    args={
        'FORCE[!]': ('-f', '--force', 'Force overwriting of target files.'),
        'TOOL_NAME': ('-T', '--tool-name', 'Tool name (default: <folder name>).'),
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
    TOOL_FOLDER: Optional[Text]


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    print(runner.tool.jiig_root_folder)
    expand_folder(
        os.path.join(runner.tool.jiig_root_folder,
                     jiig.const.TOOL_TEMPLATES_FOLDER,
                     'script'),
        data.TOOL_FOLDER,
        overwrite=data.FORCE,
        symbols={
            'mytool': (data.TOOL_NAME or os.path.basename(data.TOOL_FOLDER)),
        },
    )
