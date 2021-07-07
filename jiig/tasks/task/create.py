"""
Task creation task.
"""

import os

import jiig
from jiig.util.template_expansion import expand_folder


@jiig.task
def create(
    runtime: jiig.Runtime,
    force: jiig.f.boolean('Force overwriting of target files.', cli_flags=('-f', '--force')),
    new_task_name: jiig.f.text('Task/module name(s).', repeat=(1, None)),
    output_folder: jiig.f.filesystem_folder('Output tasks folder for generated modules.',
                                            absolute_path=True,
                                            cli_flags=('-o', '--output-folder'),
                                            ) = '.',
):
    """Create task module(s)."""
    if not os.path.exists(os.path.join(output_folder, '../__init__.py')):
        runtime.abort(f'Target folder is not a Python package.', output_folder)
    source_folder = os.path.join(runtime.tool.jiig_root_folder, 'templates/task')
    for task_name in new_task_name:
        runtime.message(f'Generating task "{task_name}".')
        expand_folder(
            source_folder,
            output_folder,
            overwrite=force,
            symbols={
                'mytask': task_name,
                'template_bool_option': f'{task_name}_bool',
                'template_string_option': f'{task_name}_string',
                'template_argument_positional': f'{task_name}_arg',
            }
        )
        runtime.message('NOTE: Make sure to link to the new task from the tool root task.')
