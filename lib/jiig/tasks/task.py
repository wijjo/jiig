"""Task creation task."""

import os
from typing import List, Text

import jiig

from jiig.utility.console import log_heading, log_message, abort
from jiig.utility.filesystem import expand_template
from jiig.utility.general import plural


@jiig.task('task',
           description='Manage task modules',
           hidden_task=True)
def task_task(runner: jiig.TaskRunner):
    if os.getcwd() == runner.params.CORE_ROOT:
        abort('Please run this command from an application folder.')


@jiig.sub_task(task_task,
               'create',
               jiig.bool_option('FORCE',
                                ('-f', '--force'),
                                description='Force overwriting of target files'),
               jiig.option('OUTPUT_FOLDER',
                           ('-o', '--output-folder'),
                           jiig.adapters.folder_path,
                           description='Output tasks folder for generated modules',
                           default_value='.'),
               jiig.argument('NEW_TASK_NAME',
                             description='Task/module name(s)',
                             cardinality='+'),
               description='Create task module(s)')
def task_task_create(runner: jiig.TaskRunner):
    tasks_folder = runner.args.OUTPUT_FOLDER or os.getcwd()
    # This check makes it more likely to put generated modules in a reasonable place.
    if not os.path.exists(os.path.join(tasks_folder, '__init__.py')):
        abort(f'Tasks folder "{tasks_folder}" is not a package (with __init__.py).',
              tasks_folder)
    log_heading(1, 'Create task module(s)')
    template_path = os.path.join(runner.params.JIIG_ROOT,
                                 runner.params.JIIG_TEMPLATES_FOLDER,
                                 runner.params.JIIG_TASK_TEMPLATE)
    skipped_files: List[Text] = []
    for task_name in runner.args.NEW_TASK_NAME:
        module_name = f'{task_name}.py'
        module_path = os.path.join(tasks_folder, module_name)
        if os.path.exists(module_path):
            if not runner.args.FORCE:
                log_message(f'Not overwriting existing task module.',
                            module_path=module_path)
                skipped_files.append(module_name)
                continue
        log_message(f'Generating task module.',
                    template_path=template_path,
                    module_path=module_path)
        expand_template(template_path,
                        module_path,
                        overwrite=runner.args.FORCE,
                        symbols={'TASK_NAME': task_name,
                                 'ARG_PREFIX': task_name.upper()})
    skipped_text = plural('file', skipped_files)
    if skipped_files:
        log_message(f'Use -f/--force to overwrite the following skipped {skipped_text}:',
                    *skipped_files)
    module_text = plural('module', runner.args.NEW_TASK_NAME)
    import_samples = [f'import <package>.{task_name}'
                      for task_name in runner.args.NEW_TASK_NAME]
    log_message(f'Remember to import the new {module_text}, e.g. in your main script, e.g.:',
                *import_samples)
