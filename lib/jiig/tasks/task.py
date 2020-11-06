"""Task creation task."""

import os

from jiig import arg, task, sub_task, TaskRunner, argument

from jiig.globals import global_data

from jiig.utility.console import log_heading, log_message, abort
from jiig.utility.filesystem import expand_template


@task('task',
      description='Manage task modules',
      hidden_task=True)
def task_task(runner: TaskRunner):
    if os.getcwd() == runner.params.CORE_ROOT:
        abort('Please run this command from an application folder.')


@sub_task(task_task, 'create',
          argument('OUTPUT_FOLDER', arg.folder_path(must_exist=True),
                   description='Generated module(s) folder',
                   default_value='.',
                   flags='-o'),
          argument('NEW_TASK_NAME', arg.text,
                   description='Task/module name(s)',
                   cardinality='+'),
          description='Create task module(s)')
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
