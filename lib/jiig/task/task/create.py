"""
Task creation task.
"""

import os
from typing import Text, List

import jiig
from jiig.util.console import log_topic, abort
from jiig.util.template_expansion import expand_folder


TASK = jiig.Task(
    description='Create task module(s).',
    args={
        'FORCE[!]': ('-f', '--force', 'Force overwriting of target files.'),
        'OUTPUT_FOLDER': ('-o', '--output-folder',
                          'Output tasks folder for generated modules.',
                          jiig.arg.path_is_folder,
                          jiig.arg.path_to_absolute,
                          jiig.arg.default('.')),
        'NEW_TASK_NAME[+]': 'Task/module name(s).',
    },
)


# For type inspection only.
class Data:
    FORCE: bool
    OUTPUT_FOLDER: Text
    NEW_TASK_NAME: List[Text]


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    if not os.path.exists(os.path.join(data.OUTPUT_FOLDER, '../__init__.py')):
        abort(f'Target folder is not a Python package.', data.OUTPUT_FOLDER)
    source_folder = os.path.join(runner.tool.jiig_root_folder,
                                 jiig.const.TASK_TEMPLATES_FOLDER)
    with log_topic('Create task module(s)') as topic:
        for task_name in data.NEW_TASK_NAME:
            topic.message(f'Generating task "{task_name}".')
            expand_folder(
                source_folder,
                data.OUTPUT_FOLDER,
                overwrite=data.FORCE,
                symbols={
                    'template_task_name': task_name,
                    'template_bool_option': f'{task_name.upper()}_BOOL',
                    'template_string_option': f'{task_name.upper()}_STRING',
                    'template_argument': f'{task_name.upper()}_ARG',
                }
            )
