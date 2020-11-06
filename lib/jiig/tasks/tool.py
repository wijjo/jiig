"""Tool creation task."""

import os
from typing import Text

from jiig import arg, task, sub_task, TaskRunner, argument

from jiig.globals import global_data

from jiig.utility.console import log_heading, abort
from jiig.utility.filesystem import expand_template_folder


@task('tool',
      description='Manage tool assets')
def task_tool(runner: TaskRunner):
    if os.getcwd() == runner.params.CORE_ROOT:
        abort('Please run this command from an application folder.')


def expand_tool_template(runner: TaskRunner, template_name: Text):
    log_heading(1, f'Create tool {template_name}')
    symbols = dict(runner.params)
    target_folder = os.path.realpath(runner.args.TOOL_FOLDER)
    symbols['TOOL_NAME'] = runner.args.TOOL_NAME or os.path.basename(target_folder)
    source_folder = os.path.join(runner.params.JIIG_ROOT,
                                 global_data.tool_templates_folder,
                                 template_name)
    expand_template_folder(source_folder,
                           target_folder,
                           overwrite=runner.args.OVERWRITE,
                           symbols=symbols)


@sub_task(task_tool, 'project',
          argument('OVERWRITE', arg.boolean,
                   description='Overwrite target files',
                   flags='-o'),
          argument('TOOL_NAME', arg.text,
                   description='Tool name (default: <folder name>)',
                   flags='-n'),
          argument('TOOL_FOLDER', arg.folder_path,
                   description='Generated tool output folder',
                   default_value='.',
                   cardinality='?'),
          description='Create Jiig tool project')
def task_tool_project(runner: TaskRunner):
    expand_tool_template(runner, 'project')


@sub_task(task_tool, 'script',
          argument('OVERWRITE', arg.boolean,
                   description='Overwrite existing script',
                   flags='-o'),
          argument('TOOL_NAME', arg.text,
                   description='Tool name (default: <folder name>)',
                   flags='-n'),
          argument('TOOL_FOLDER', arg.folder_path,
                   description='Generated tool output folder',
                   default_value='.',
                   cardinality='?'),
          description='Create monolithic Jiig tool script')
def task_create_tool(runner: TaskRunner):
    expand_tool_template(runner, 'script')
