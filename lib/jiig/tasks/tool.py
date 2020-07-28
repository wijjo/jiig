import os

from jiig import task, TaskRunner
from jiig.utility import log_heading, abort, expand_template_folder
from jiig import constants


@task('tool', help='manage tool assets')
def task_tool(runner: TaskRunner):
    if os.getcwd() == runner.params.CORE_ROOT:
        abort('Please run this command from an application folder.')


@task(
    'create',
    parent=task_tool,
    help='create Jiig tool skeleton',
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
def task_create_tool(runner: TaskRunner):
    log_heading(1, 'Create tool skeleton')
    source_folder = os.path.join(runner.params.JIIG_ROOT, constants.TOOL_TEMPLATE_FOLDER)
    target_folder = os.path.realpath(runner.args.TOOL_FOLDER)
    symbols = dict(runner.params)
    symbols['TOOL_NAME'] = runner.args.TOOL_NAME or os.path.basename(target_folder)
    expand_template_folder(source_folder,
                           target_folder,
                           overwrite=runner.args.OVERWRITE,
                           symbols=symbols)
