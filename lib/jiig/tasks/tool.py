"""Tool creation task."""

import os
from typing import Text, Optional

import jiig

from jiig.utility.console import abort
from jiig.utility.template_expansion import expand_folder


class ToolProjectTask(jiig.Task):
    """Create Jiig tool project."""

    # For type inspection only.
    class Data:
        FORCE: bool
        TOOL_NAME: Text
        TASK_NAME: Text
        TOOL_FOLDER: Optional[Text]
    data: Data

    args = {
        'FORCE!': ('-f', '--force', 'Force overwriting of target files.'),
        'TOOL_NAME': ('-T', '--tool-name', 'Tool name (default: <folder name>).'),
        'TASK_NAME': ('-t', '--task-name', 'Task name (default: "task").',
                      jiig.Default('task')),
        'TOOL_FOLDER?': ('Generated tool output folder.',
                         jiig.path.check_folder,
                         jiig.path.absolute,
                         jiig.Default('.')),
    }

    def on_run(self):
        expand_folder(
            os.path.join(self.params.JIIG_ROOT,
                         self.params.TOOL_TEMPLATES_FOLDER,
                         'project'),
            self.data.TOOL_FOLDER,
            overwrite=self.data.FORCE,
            symbols={
                'template_tool_name': (self.data.TOOL_NAME
                                       or os.path.basename(self.data.TOOL_FOLDER)),
                'template_task_name': self.data.TASK_NAME,
            },
        )


class ToolScriptTask(jiig.Task):
    """Create monolithic Jiig tool script."""

    # For type inspection only.
    class Data:
        FORCE: bool
        TOOL_NAME: Text
        TOOL_FOLDER: Optional[Text]
    data: Data

    args = {
        'FORCE!': ('-f', '--force', 'Force overwriting of target files.'),
        'TOOL_NAME': ('-T', '--tool-name', 'Tool name (default: <folder name>).'),
        'TOOL_FOLDER?': ('Generated tool output folder.',
                         jiig.path.check_folder,
                         jiig.path.absolute,
                         jiig.Default('.')),
    }

    def on_run(self):
        expand_folder(
            os.path.join(self.params.JIIG_ROOT,
                         self.params.TOOL_TEMPLATES_FOLDER,
                         'script'),
            self.data.TOOL_FOLDER,
            overwrite=self.data.FORCE,
            symbols={
                'template_tool_name': (self.data.TOOL_NAME
                                       or os.path.basename(self.data.TOOL_FOLDER)),
            },
        )


class TaskClass(jiig.Task):
    """Manage tool assets."""

    sub_tasks = {
        'project': ToolProjectTask,
        'script': ToolScriptTask,
    }

    def on_run(self):
        if os.getcwd() == self.params.CORE_ROOT:
            abort('Please run this command from an application folder.')
