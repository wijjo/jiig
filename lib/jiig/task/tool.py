"""Tool creation task."""

import os
from typing import Text, Optional

from jiig import arg, const, model
from jiig.util.console import abort
from jiig.util.template_expansion import expand_folder


class ToolProjectTask(model.Task):
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
                      arg.default('task')),
        'TOOL_FOLDER?': ('Generated tool output folder.',
                         arg.path_is_folder,
                         arg.path_to_absolute,
                         arg.default('.')),
    }

    def on_run(self):
        expand_folder(
            os.path.join(self.configuration.jiig_root_folder,
                         const.TOOL_TEMPLATES_FOLDER,
                         'project'),
            self.data.TOOL_FOLDER,
            overwrite=self.data.FORCE,
            symbols={
                'template_tool_name': (self.data.TOOL_NAME
                                       or os.path.basename(self.data.TOOL_FOLDER)),
                'template_task_name': self.data.TASK_NAME,
            },
        )


class ToolScriptTask(model.Task):
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
                         arg.path_is_folder,
                         arg.path_to_absolute,
                         arg.default('.')),
    }

    def on_run(self):
        expand_folder(
            os.path.join(self.configuration.jiig_root_folder,
                         const.TOOL_TEMPLATES_FOLDER,
                         'script'),
            self.data.TOOL_FOLDER,
            overwrite=self.data.FORCE,
            symbols={
                'template_tool_name': (self.data.TOOL_NAME
                                       or os.path.basename(self.data.TOOL_FOLDER)),
            },
        )


class TaskClass(model.Task):
    """Manage tool assets."""

    sub_tasks = {
        'project': ToolProjectTask,
        'script': ToolScriptTask,
    }

    def on_run(self):
        if os.getcwd() == self.configuration.jiig_root_folder:
            abort('Please run this command from an application folder.')
