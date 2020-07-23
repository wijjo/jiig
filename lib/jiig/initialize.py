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
from typing import Text

from . import constants, init_file, utility

INIT_PARAM_TYPES = [
    init_file.ParamFolder('BASE_FOLDER'),
    init_file.ParamFolder('VENV_ROOT'),
    init_file.ParamFolderList('LIB_FOLDERS'),
    init_file.ParamFolderList('TASK_FOLDERS'),
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


def initialize_tool(name: Text, description: Text, root: Text):
    """
    Perform all steps to execute the tool application.

    :param name: tool name for help, etc.
    :param description: tool description for help, etc.
    :param root: tool base folder
    """
    jiig_init_path = get_jiig_init_path()
    tool_init_path = get_tool_init_path(root)
    all_params = init_file.load_files(INIT_PARAM_TYPES, jiig_init_path, tool_init_path)
    all_params['TOOL_NAME'] = name or os.path.basename(sys.argv[0])
    all_params['TOOL_DESCRIPTION'] = description or '(no TOOL_DESCRIPTION provided)'
    all_params['JIIG_ROOT'] = JIIG_ROOT
    # Separate tool init parameters help with checking for non-inheritable tasks.
    tool_params = init_file.load_files(INIT_PARAM_TYPES, tool_init_path)
    if all_params.VENV_ROOT:
        # Re-execute inside the virtual environment or continue.
        virtual_environment_check(all_params)
        # Should not get here if not in the virtual environment.
        venv_python_path = os.path.join(all_params.VENV_ROOT, 'bin', 'python')
        if sys.executable != venv_python_path:
            utility.abort('Not executing inside the expected virtual environment.')
    # Import is done here, inside the virtual environment, in case the virtual
    # environment is needed for resolving external task module dependencies.
    from .main import main
    main(all_params, tool_params=tool_params)


def initialize_jiig():
    """
    Initialize main Jiig application.

    This is specifically for the "jiig" command. Use `initialize_tool()` instead
    of this function for initializing a Jiig-based tool.
    """
    jiig_init_path = get_jiig_init_path()
    params = init_file.load_files(INIT_PARAM_TYPES, jiig_init_path)
    params['TOOL_NAME'] = os.path.basename(sys.argv[0])
    params['TOOL_DESCRIPTION'] = 'Jiig tool management commands.'
    params['JIIG_ROOT'] = JIIG_ROOT
    # This import can't be global. See comment in `initialize_tool()`.
    from .main import main
    main(params)
