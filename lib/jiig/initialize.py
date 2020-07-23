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


def get_jiig_init_path() -> Text:
    # If running a *IX system-installed copy, find the init file in a parallel etc folder.
    if os.path.sep == '/' and JIIG_LIB_FOLDER.startswith('/'):
        for jiig_sys_folder in ['/usr/local/etc/jiig', '/etc/jiig']:
            init_path = os.path.join(jiig_sys_folder, constants.INIT_FILE)
            if os.path.isfile(init_path):
                return init_path
    init_path = os.path.join(JIIG_ROOT, constants.INIT_FILE)
    if os.path.isfile(init_path):
        return init_path
    utility.abort(f'Jiig init file, "{constants.INIT_FILE}", not found.')


def get_tool_init_path(root: Text) -> Text:
    init_path = os.path.join(root, constants.INIT_FILE)
    if os.path.isfile(init_path):
        return init_path
    utility.abort(f'Jiig tool init file, "{init_path}", not found.')


def initialize_tool(name: Text, description: Text, root: Text, task_folders: List[Text]):
    """
    Perform all steps to execute the tool application.

    :param name: tool name for help, etc.
    :param description: tool description for help, etc.
    :param root: tool base folder
    :param task_folders: list of folders with task modules
    """
    params = init_file.load_files(INIT_PARAM_TYPES, get_tool_init_path(root))
    tool_root = os.path.realpath(root)
    params['TOOL_ROOT'] = tool_root
    params['TOOL_NAME'] = name or os.path.basename(sys.argv[0])
    params['TOOL_DESCRIPTION'] = description or '(no TOOL_DESCRIPTION provided)'
    params['JIIG_ROOT'] = JIIG_ROOT
    params['LIB_FOLDERS'] = list(utility.resolve_paths_abs(tool_root, params['LIB_FOLDERS']))
    params['TASK_FOLDERS'] = list(utility.resolve_paths_abs(tool_root, task_folders))
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
    from .main import main
    main(params)
