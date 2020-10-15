"""Task creation task."""

import os

from jiig import task, TaskRunner
from jiig.internal import global_data
from jiig.utility.console import log_heading, log_message, abort
from jiig.utility.filesystem import expand_template


@task('task',
      help='manage task modules',
      hidden_task=True)
def task_task(runner: TaskRunner):
    if os.getcwd() == runner.params.CORE_ROOT:
        abort('Please run this command from an application folder.')


@task(
    'create',
    parent=task_task,
    help='create task module(s)',
    options=[
        ('-o', {'dest': 'OUTPUT_FOLDER',
                'help': 'folder for generated module(s) (default: working folder)'}),
    ],
    arguments=[
        {'dest': 'NEW_TASK_NAME',
         'nargs': '+',
         'help': 'task/module name(s)'},
    ],
)
def task_task_create(runner: TaskRunner):
    log_heading(1, 'Create task module(s)')
    output_folder = runner.params.OUTPUT_FOLDER or os.getcwd()
    template_path = os.path.join(runner.params.JIIG_ROOT,
                                 global_data.templates_folder,
                                 global_data.task_template)
    for task_name in runner.args.NEW_TASK_NAME:
        module_name = f'{task_name}.py'
        module_path = os.path.join(output_folder, module_name)
        if os.path.exists(module_path):
            if not runner.args.OVERWRITE:
                log_message(f'Not overwriting existing task module.',
                            module_path=module_path)
                continue
        log_message(f'Generating task module.',
                    template_path=template_path,
                    module_path=module_path)
        expand_template(template_path, module_path, symbols={'TASK_NAME': task_name})
        log_message(f'Remember to import the new module, e.g. in your main script.')
