from jiig.task import map_task, TaskRunner
from jiig import utility


@map_task(
    'venv',
    help='build the virtual environment',
    options={'-r': {
        'dest': 'REBUILD_VENV',
        'action': 'store_true',
        'help': 'force virtual environment rebuild'}},
    description='Build the Python virtual environment.')
def task_venv(runner: TaskRunner):
    if runner.params.PRIMARY_TASK:
        utility.display_heading(1, 'Build virtual environment')
    utility.build_virtual_environment(runner.params.VENV_FOLDER,
                                      packages=runner.params.PIP_PACKAGES,
                                      rebuild=runner.args.REBUILD_VENV,
                                      quiet=not runner.params.PRIMARY_TASK)
