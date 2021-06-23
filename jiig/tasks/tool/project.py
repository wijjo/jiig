"""
Tool project creation task.
"""

import os

import jiig
from jiig.util.template_expansion import expand_folder


DEFAULT_TASK_NAME = 'mytask'


# For type inspection only.
class Task(jiig.Task):
    """Create Jiig tool project."""

    force: jiig.f.boolean('Force overwriting of target files.',
                          cli_flags=('-f', '--force'))
    tool_name: jiig.f.text('Tool name (default: <folder name>).',
                           cli_flags=('-T', '--tool-name'))
    task_name: jiig.f.text(f'Task name (default: "{DEFAULT_TASK_NAME}").',
                           cli_flags=('-t', '--task-name')) = DEFAULT_TASK_NAME
    tool_folder: jiig.f.filesystem_folder('Generated tool output folder.',
                                          absolute_path=True) = '.'

    def on_run(self, runtime: jiig.Runtime):
        expand_folder(
            os.path.join(runtime.tool.jiig_root_folder, 'templates/tool/project'),
            self.tool_folder,
            overwrite=self.force,
            symbols={
                'jiig_root': runtime.tool.jiig_root_folder,
                'mytool': (self.tool_name or os.path.basename(self.tool_folder)),
                'mytask': self.task_name,
            },
        )
