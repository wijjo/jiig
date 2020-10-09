import os
from typing import Text

from jiig import task, TaskRunner
from jiig.internal import global_data
from jiig.utility.console import log_heading, abort
from jiig.utility.filesystem import expand_template_folder


@task('tool',
      help='manage tool assets')
def task_tool(runner: TaskRunner):
    if os.getcwd() == runner.params.CORE_ROOT:
        abort('Please run this command from an application folder.')


def expand_tool_template(runner: TaskRunner, template_name: Text):
    log_heading(1, f'Create tool {template_name}')
    symbols = dict(runner.params)
    target_folder = os.path.realpath(runner.args.TOOL_FOLDER)
    symbols['TOOL_NAME'] = runner.args.TOOL_NAME or os.path.basename(target_folder)
    source_folder = os.path.join(runner.params.JIIG_ROOT,
                                 global_data.TOOL_TEMPLATES_FOLDER,
                                 template_name)
    expand_template_folder(source_folder,
                           target_folder,
                           overwrite=runner.args.OVERWRITE,
                           symbols=symbols)


@task(
    'project',
    parent=task_tool,
    help='create Jiig tool project',
    options={
        '-o': {'dest': 'OVERWRITE',
               'action': 'store_true',
               'help': 'overwrite target files'},
        '-n': {'dest': 'TOOL_NAME',
               'help': 'tool name (default=<folder name>)'},
    },
    arguments=[
        {'dest': 'TOOL_FOLDER',
         'nargs': '?',
         'default': os.getcwd(),
         'help': 'output folder for generated tool (default=".")'},
    ],
)
def task_tool_project(runner: TaskRunner):
    expand_tool_template(runner, 'project')


@task(
    'script',
    parent=task_tool,
    help='create monolithic Jiig tool script',
    options={
        '-o': {'dest': 'OVERWRITE',
               'action': 'store_true',
               'help': 'overwrite existing script'},
        '-n': {'dest': 'TOOL_NAME',
               'help': 'tool name (default=<folder name>)'},
    },
    arguments=[
        {'dest': 'TOOL_FOLDER',
         'nargs': '?',
         'default': os.getcwd(),
         'help': 'output folder for generated tool (default=".")'},
    ],
)
def task_create_tool(runner: TaskRunner):
    expand_tool_template(runner, 'script')
