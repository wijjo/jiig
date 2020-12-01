"""Tool creation task."""

import os
from typing import Text

import jiig

from jiig.utility.console import log_heading, abort
from jiig.utility.filesystem import expand_template_folder


@jiig.task('tool',
           description='Manage tool assets')
def task_tool(runner: jiig.TaskRunner):
    if os.getcwd() == runner.params.CORE_ROOT:
        abort('Please run this command from an application folder.')


def expand_tool_template(runner: jiig.TaskRunner, template_type_name: Text):
    log_heading(1, f'Create tool {template_type_name}')
    target_folder = os.path.realpath(runner.args.TOOL_FOLDER)
    source_folder = os.path.join(runner.params.JIIG_ROOT,
                                 runner.params.TOOL_TEMPLATES_FOLDER,
                                 template_type_name)
    tool_name = runner.args.TOOL_NAME or os.path.basename(target_folder)
    expand_template_folder(source_folder,
                           target_folder,
                           overwrite=runner.args.OVERWRITE,
                           symbols=dict(runner.params, TOOL_NAME=tool_name))


@jiig.sub_task(task_tool,
               'project',
               jiig.bool_option('FORCE',
                                ('-f', '--force'),
                                description='Force overwriting of target files'),
               jiig.option('TOOL_NAME',
                           ('-n', '--name'),
                           description='Tool name (default: <folder name>)'),
               jiig.argument('TOOL_FOLDER',
                             jiig.adapters.folder_path,
                             description='Generated tool output folder',
                             default_value='.',
                             cardinality='?'),
               description='Create Jiig tool project')
def task_tool_project(runner: jiig.TaskRunner):
    expand_tool_template(runner, 'project')


@jiig.sub_task(task_tool,
               'script',
               jiig.bool_option('FORCE',
                                ('-o', '--overwrite'),
                                description='Overwrite existing script'),
               jiig.option('TOOL_NAME',
                           ('-n', '--name'),
                           description='Tool name (default: <folder name>)'),
               jiig.argument('TOOL_FOLDER',
                             jiig.adapters.folder_path,
                             description='Generated tool output folder',
                             default_value='.',
                             cardinality='?'),
               description='Create monolithic Jiig tool script')
def task_create_tool(runner: jiig.TaskRunner):
    expand_tool_template(runner, 'script')
