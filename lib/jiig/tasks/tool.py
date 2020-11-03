"""Tool creation task."""

import os
from typing import Text

import jiig

from jiig.internal import global_data
from jiig.utility.console import log_heading, abort
from jiig.utility.filesystem import expand_template_folder


@jiig.task(
    'tool',
    description='Manage tool assets',
)
def task_tool(runner: jiig.TaskRunner):
    if os.getcwd() == runner.params.CORE_ROOT:
        abort('Please run this command from an application folder.')


def expand_tool_template(runner: jiig.TaskRunner, template_name: Text):
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


@jiig.sub_task(
    task_tool, 'project',
    jiig.Arg('OVERWRITE', jiig.arg.Boolean,
             description='Overwrite target files',
             flags='-o'),
    jiig.Arg('TOOL_NAME', jiig.arg.String,
             description='Tool name (default: <folder name>)',
             flags='-n'),
    jiig.Arg('TOOL_FOLDER', jiig.arg.Folder,
             description='Generated tool output folder',
             default_value='.',
             cardinality='?'),
    description='Create Jiig tool project',
)
def task_tool_project(runner: jiig.TaskRunner):
    expand_tool_template(runner, 'project')


@jiig.sub_task(
    task_tool, 'script',
    jiig.Arg('OVERWRITE', jiig.arg.Boolean,
             description='Overwrite existing script',
             flags='-o'),
    jiig.Arg('TOOL_NAME', jiig.arg.String,
             description='Tool name (default: <folder name>)',
             flags='-n'),
    jiig.Arg('TOOL_FOLDER', jiig.arg.Folder,
             description='Generated tool output folder',
             default_value='.',
             cardinality='?'),
    description='Create monolithic Jiig tool script',
)
def task_create_tool(runner: jiig.TaskRunner):
    expand_tool_template(runner, 'script')
