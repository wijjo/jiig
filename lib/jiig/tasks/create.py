import os

from jiig.task import map_task, TaskRunner
from jiig.utility import display_heading, display_message, abort,\
    expand_template_folder, expand_template
from jiig import constants


@map_task('create', help='create tool assets')
def task_create(runner: TaskRunner):
    if os.getcwd() == runner.params.CORE_ROOT:
        abort('Please run this command from an application folder.')


@map_task(
    'tool',
    parent=task_create,
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
    options={
        '-o': {'dest': 'OUTPUT_FOLDER',
               'help': 'folder for generated module(s) (default: working folder)'},
    },
    arguments=[
        {'dest': 'NEW_TASK_NAME',
         'nargs': '+',
         'help': 'task/module name(s)'},
    ],
)
def task_create_task(runner: TaskRunner):
    display_heading(1, 'Create task module(s)')
    output_folder = runner.params.OUTPUT_FOLDER or os.getcwd()
    template_path = os.path.join(runner.params.JIIG_ROOT,
                                 constants.TEMPLATES_FOLDER,
                                 constants.TASK_TEMPLATE)
    for task_name in runner.args.NEW_TASK_NAME:
        module_name = f'{task_name}.py'
        module_path = os.path.join(output_folder, module_name)
        if os.path.exists(module_path):
            if not runner.args.OVERWRITE:
                display_message(f'Not overwriting existing task module.',
                                module_path=module_path)
                continue
        display_message(f'Generating task module.',
                        template_path=template_path,
                        module_path=module_path)
        expand_template(template_path, module_path, symbols={'TASK_NAME': task_name})
