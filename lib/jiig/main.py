"""
Jiig initialization.

This is a bit of a "magic" module that is responsible for:

- Loading Jiig application configuration parameters.
- Building a custom virtual environment as needed.
- Restarting the application inside the virtual environment.
-
"""
import sys
import os
from typing import Text, List

from . import constants, init_file, utility

INIT_PARAM_TYPES = [
    init_file.ParamFolderList('LIB_FOLDERS'),
    init_file.ParamFolder('VENV_ROOT'),
    init_file.ParamList('PIP_PACKAGES', unique=True, default_value=[]),
]

SAMPLE_INIT_FILE = '''\
LIB_FOLDERS = ['jiig']
VENV_ROOT = 'venv'
PIP_PACKAGES = []
'''


JIIG_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
JIIG_LIB_FOLDER = os.path.dirname(os.path.realpath(__file__))


def virtual_environment_check(params: init_file.ParamData):
    """Make sure we're running in the virtual environment or return if we are."""
    venv_python_path = os.path.join(params.VENV_ROOT, 'bin', 'python')
    if sys.executable != venv_python_path:
        utility.build_virtual_environment(params.VENV_ROOT,
                                          packages=params.PIP_PACKAGES,
                                          rebuild=False,
                                          quiet=True)
        # Replace process with one invoked in the virtual environment.
        os.execlp(venv_python_path, venv_python_path, *sys.argv)


def get_tool_init_path(root: Text) -> Text:
    init_path = os.path.join(root, constants.INIT_FILE)
    if os.path.isfile(init_path):
        return init_path
    utility.display_error(f'Jiig tool init file, "{init_path}", not found.')
    try:
        with open(init_path, 'w', encoding='utf-8') as file_handle:
            file_handle.write(SAMPLE_INIT_FILE)
    except (IOError, OSError) as exc:
        utility.display_error(f'Unable to save sample "{init_path}: {exc}')
    utility.abort(f'Edit "{init_path}" before re-running.')


def jiig_main():
    """
    Perform all steps to execute the core "jiig" program.
    """
    from .tool_runner import run_tool
    try:
        run_tool({
            'TOOL_NAME': 'jiig',
            'TOOL_DESCRIPTION': 'Jiig tool management commands.',
            'JIIG_ROOT': JIIG_ROOT,
            'LIB_FOLDERS': list(utility.resolve_paths_abs(JIIG_ROOT, ['lib'])),
            'TASK_FOLDERS': list(utility.resolve_paths_abs(JIIG_ROOT, ['tasks'])),
        })
    except KeyboardInterrupt:
        print('')


def tool_main(*,
              name: Text = None,
              description: Text = None,
              root: Text = None,
              task_folders: List[Text] = None):
    """
    Perform all steps to execute the tool application.

    :param name: tool name for help, etc.
    :param description: tool description for help, etc.
    :param root: tool base folder
    :param task_folders: list of folders with task modules
    """
    tool_name = name or os.path.basename(sys.argv[0])
    tool_root = os.path.realpath(root) if root else os.path.dirname(sys.argv[0])
    params = init_file.load_files(INIT_PARAM_TYPES, get_tool_init_path(tool_root))
    tool_description = description or '(no TOOL_DESCRIPTION provided)'
    lib_folders = list(utility.resolve_paths_abs(tool_root, params['LIB_FOLDERS']))
    task_folders = list(utility.resolve_paths_abs(tool_root, task_folders))
    params['TOOL_NAME'] = tool_name
    params['TOOL_DESCRIPTION'] = tool_description
    params['TOOL_ROOT'] = tool_root
    params['JIIG_ROOT'] = JIIG_ROOT
    params['LIB_FOLDERS'] = lib_folders
    params['TASK_FOLDERS'] = task_folders
    # Separate tool init parameters help with checking for non-inheritable tasks.
    if params.VENV_ROOT:
        # Re-execute inside the virtual environment or continue.
        virtual_environment_check(params)
        # Should not get here if not in the virtual environment.
        venv_python_path = os.path.join(params.VENV_ROOT, 'bin', 'python')
        if sys.executable != venv_python_path:
            utility.abort('Not executing inside the expected virtual environment.')
    # Import is done here, inside the virtual environment, in case the virtual
    # environment is needed for resolving external task module dependencies.
    from .tool_runner import run_tool
    try:
        run_tool(params)
    except KeyboardInterrupt:
        print('')
