"""
Tool project creation task.
"""

import os

import jiig
from jiig.util.template_expansion import expand_folder


DEFAULT_TASK_NAME = 'mytask'


@jiig.task
def project(
    runtime: jiig.Runtime,
    force: jiig.f.boolean('Force overwriting of target files.',
                          cli_flags=('-f', '--force')),
    tool_name: jiig.f.text('Tool name (default: <folder name>).',
                           cli_flags=('-T', '--tool-name')),
    task_name: jiig.f.text(f'Task name (default: "{DEFAULT_TASK_NAME}").',
                           cli_flags=('-t', '--task-name')) = DEFAULT_TASK_NAME,
    tool_folder: jiig.f.filesystem_folder('Generated tool output folder.',
                                          absolute_path=True) = '.',
):
    """Create Jiig tool project."""
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
