"""
Task creation task.
"""

import os
from typing import Text, List

import jiig
from jiig.utility.console import log_topic, abort
from jiig.utility.template_expansion import expand_folder


class TaskCreateTask(jiig.Task):
    """Create task module(s)."""

    # For type inspection only.
    class Data:
        FORCE: bool
        OUTPUT_FOLDER: Text
        NEW_TASK_NAME: List[Text]
    data: Data

    args = {
        'FORCE!': ('-f', '--force', 'Force overwriting of target files.'),
        'OUTPUT_FOLDER': ('-o', '--output-folder',
                          'Output tasks folder for generated modules.',
                          jiig.path.check_folder,
                          jiig.path.absolute,
                          jiig.Default('.')),
        'NEW_TASK_NAME[+]': 'Task/module name(s).',
    }

    def on_run(self):
        if not os.path.exists(os.path.join(self.data.OUTPUT_FOLDER, '__init__.py')):
            abort(f'Target folder is not a Python package.',
                  self.data.OUTPUT_FOLDER)
        source_folder = os.path.join(self.params.JIIG_ROOT,
                                     self.params.TASK_TEMPLATES_FOLDER)
        with log_topic('Create task module(s)') as topic:
            for task_name in self.data.NEW_TASK_NAME:
                topic.message(f'Generating task "{task_name}".')
                expand_folder(
                    source_folder,
                    self.data.OUTPUT_FOLDER,
                    overwrite=self.data.FORCE,
                    symbols={
                        'template_task_name': task_name,
                        'template_bool_option': f'{task_name.upper()}_BOOL',
                        'template_string_option': f'{task_name.upper()}_STRING',
                        'template_argument': f'{task_name.upper()}_ARG',
                    }
                )


class TaskClass(jiig.Task):
    """Manage task modules."""

    sub_tasks = {
        'create': TaskCreateTask,
    }

    def on_run(self):
        pass
