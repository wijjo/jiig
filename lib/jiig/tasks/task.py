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

    args = [
        jiig.BoolOpt(('-f', '--force'), 'FORCE',
                     description='Force overwriting of target files.'),
        jiig.Opt(('-o', '--output-folder'), 'OUTPUT_FOLDER',
                 'Output tasks folder for generated modules.',
                 jiig.adapters.path.check_folder,
                 default_value='.'),
        jiig.Arg('NEW_TASK_NAME', 'Task/module name(s).', cardinality='+'),
    ]

    def on_run(self):
        target_folder = self.data.OUTPUT_FOLDER or os.getcwd()
        if not os.path.exists(os.path.join(target_folder, '__init__.py')):
            abort(f'Target folder "{target_folder}" is not a Python package.',
                  target_folder)
        with log_topic('Create task module(s)') as topic:
            source_folder = os.path.join(self.params.JIIG_ROOT,
                                         self.params.TASK_TEMPLATES_FOLDER)
            for task_name in self.data.NEW_TASK_NAME:
                topic.message(f'Generating task "{task_name}".')
                expand_folder(source_folder,
                              target_folder,
                              overwrite=self.data.FORCE,
                              symbols={
                                  'template_task_name': task_name,
                                  'template_bool_option': f'{task_name.upper()}_BOOL',
                                  'template_string_option': f'{task_name.upper()}_STRING',
                                  'template_argument': f'{task_name.upper()}_ARG',
                              })


class TaskClass(jiig.Task):
    """Manage task modules."""

    sub_tasks = {
        'create': TaskCreateTask,
    }

    def on_run(self):
        pass
