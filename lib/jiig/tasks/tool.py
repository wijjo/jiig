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

    args = [
        jiig.BoolOpt(('-f', '--force'), 'FORCE', 'Force overwriting of target files.'),
        jiig.Opt(('-T', '--tool-name'), 'TOOL_NAME', 'Tool name (default: <folder name>).'),
        jiig.Opt(('-t', '--task-name'), 'TASK_NAME', 'Task name (default: "task").'),
        jiig.Arg('TOOL_FOLDER',
                 'Generated tool output folder.',
                 jiig.adapters.path.check_folder,
                 default_value='.',
                 cardinality='?'),
    ]

    def on_run(self):
        target_folder = os.path.realpath(self.data.TOOL_FOLDER)
        source_folder = os.path.join(self.params.JIIG_ROOT,
                                     self.params.TOOL_TEMPLATES_FOLDER,
                                     'project')
        tool_name = self.data.TOOL_NAME or os.path.basename(target_folder)
        task_name = self.data.TASK_NAME or 'task'
        expand_folder(source_folder,
                      target_folder,
                      overwrite=self.data.FORCE,
                      symbols={'template_tool_name': tool_name,
                               'template_task_name': task_name},
                      )


class ToolScriptTask(jiig.Task):
    """Create monolithic Jiig tool script."""

    # For type inspection only.
    class Data:
        FORCE: bool
        TOOL_NAME: Text
        TOOL_FOLDER: Optional[Text]
    data: Data

    args = [
        jiig.BoolOpt(('-f', '--force'), 'FORCE', 'Force overwriting of target files.'),
        jiig.Opt(('-n', '--name'), 'TOOL_NAME', 'Tool name (default: <folder name>).'),
        jiig.Arg('TOOL_FOLDER',
                 'Generated tool output folder.',
                 jiig.adapters.path.check_folder,
                 default_value='.',
                 cardinality='?'),
    ]

    def on_run(self):
        target_folder = os.path.realpath(self.data.TOOL_FOLDER)
        tool_name = self.data.TOOL_NAME or os.path.basename(target_folder)
        source_folder = os.path.join(self.params.JIIG_ROOT,
                                     self.params.TOOL_TEMPLATES_FOLDER,
                                     'script')
        expand_folder(source_folder,
                      target_folder,
                      overwrite=self.data.FORCE,
                      symbols={'template_tool_name': tool_name},
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
