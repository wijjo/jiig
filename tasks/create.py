import os

from jiig.task import map_task, TaskRunner
from jiig.utility import display_heading, display_message, abort,\
    expand_template_folder, expand_template
from jiig import constants


@map_task(
    'create',
    help='create tool assets',
    description='Create various tool asset types. See sub-tasks for specifics.',
)
def task_create(runner: TaskRunner):
    if os.getcwd() == runner.params.CORE_ROOT:
        abort('Please run this command from an application folder.')


@map_task(
    'tool',
    parent=task_create,
    help='create Jiig tool skeleton',
    description='Create or update Jiig tool files.',
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
    display_heading(1, 'Create tool skeleton')
    source_folder = os.path.join(runner.params.JIIG_ROOT, constants.TOOL_TEMPLATE_FOLDER)
    target_folder = os.path.realpath(runner.args.TOOL_FOLDER)
    symbols = dict(runner.params)
    symbols['TOOL_NAME'] = runner.args.TOOL_NAME or os.path.basename(target_folder)
    expand_template_folder(source_folder,
                           target_folder,
                           overwrite=runner.args.OVERWRITE,
                           symbols=symbols)


@map_task(
    'task',
    parent=task_create,
    help='create task module(s)',
    description='Create new Jiig tool task module.',
    options={
        '-o': {'dest': 'OVERWRITE',
               'action': 'store_true',
               'help': 'overwrite target file'},
    },
    arguments=[
        {'dest': 'NEW_TASK_NAME',
         'nargs': '+',
         'help': 'task/module name(s)'},
    ],
)
def task_create_task(runner: TaskRunner):
    display_heading(1, 'Create task module(s)')
    # TODO: Need more control over which task folder to choose if multiple?
    task_folder = runner.params.TASK_FOLDERS[0]
    template_path = os.path.join(runner.params.JIIG_ROOT,
                                 constants.TEMPLATES_FOLDER,
                                 constants.TASK_TEMPLATE)
    for task_name in runner.args.NEW_TASK_NAME:
        module_name = f'{task_name}.py'
        module_path = os.path.join(task_folder, module_name)
        if os.path.exists(module_path):
            if not runner.args.OVERWRITE:
                display_message(f'Not overwriting existing task module.',
                                module_path=module_path)
                continue
        display_message(f'Generating task module.',
                        template_path=template_path,
                        module_path=module_path)
        expand_template(template_path, module_path, symbols={'TASK_NAME': task_name})
