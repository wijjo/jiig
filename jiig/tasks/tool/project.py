"""
Tool project creation task.
"""

import os

import jiig
from jiig.util.template_expansion import expand_folder


DEFAULT_TASK_NAME = 'mytask'


@jiig.task(
    cli={
        'options': {
            'force': ('-f', '--force'),
            'tool_name': ('-T', '--tool-name'),
            'task_name': ('-t', '--task-name'),
        }
    }
)
def project(
    runtime: jiig.Runtime,
    force: jiig.f.boolean(),
    tool_name: jiig.f.text(),
    task_name: jiig.f.text() = DEFAULT_TASK_NAME,
    tool_folder: jiig.f.filesystem_folder(absolute_path=True) = '.',
):
    """
    Create Jiig tool project.

    :param runtime: Jiig runtime API.
    :param force: Force overwriting of target files.
    :param tool_name: Tool name (default: <folder name>).
    :param task_name: Task name (default: "{DEFAULT_TASK_NAME}").
    :param tool_folder: Generated tool output folder.
    """
    expand_folder(
        os.path.join(runtime.tool.jiig_root_folder, 'templates/tool/project'),
        tool_folder,
        overwrite=force,
        symbols={
            'jiig_root': runtime.tool.jiig_root_folder,
            'mytool': tool_name or os.path.basename(tool_folder),
            'mytask': task_name,
        },
    )
