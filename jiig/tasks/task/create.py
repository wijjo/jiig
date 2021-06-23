"""
Task creation task.
"""

import os

import jiig
from jiig.util.console import abort, log_message
from jiig.util.template_expansion import expand_folder


class Task(jiig.Task):
    """Create task module(s)."""

    force: jiig.f.boolean('Force overwriting of target files.', cli_flags=('-f', '--force'))
    new_task_name: jiig.f.text('Task/module name(s).', repeat=(1, None))
    output_folder: jiig.f.filesystem_folder('Output tasks folder for generated modules.',
                                            absolute_path=True,
                                            cli_flags=('-o', '--output-folder'),
                                            ) = '.'

    def on_run(self, runtime: jiig.Runtime):
        if not os.path.exists(os.path.join(self.output_folder, '../__init__.py')):
            abort(f'Target folder is not a Python package.', self.output_folder)
        source_folder = os.path.join(runtime.tool.jiig_root_folder, 'templates/task')
        for task_name in self.new_task_name:
            log_message(f'Generating task "{task_name}".')
            expand_folder(
                source_folder,
                self.output_folder,
                overwrite=self.force,
                symbols={
                    'mytask': task_name,
                    'template_bool_option': f'{task_name}_bool',
                    'template_string_option': f'{task_name}_string',
                    'template_argument_positional': f'{task_name}_arg',
                }
            )
            log_message('NOTE: Make sure to link to the new task from the tool root task.')
