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
    init_file.ParamString('APP_NAME'),
    init_file.ParamFolder('BASE_FOLDER'),
    init_file.ParamFolder('VENV_FOLDER'),
    init_file.ParamFolderList('LIB_FOLDERS'),
    init_file.ParamList('PIP_PACKAGES', unique=True, default_value=[]),
]


def load_configuration(folders: List[Text]) -> init_file.ParamData:
    """Load and return Jiig configuration parameters."""
    return init_file.load(INIT_PARAM_TYPES, folders, constants.INIT_FILE)


def virtual_environment_check(params: init_file.ParamData):
    """Make sure we're running in the virtual environment or return if we are."""
    venv_python_path = os.path.join(params.VENV_FOLDER, 'bin', 'python')
    if sys.executable != venv_python_path:
        utility.build_virtual_environment(params.VENV_FOLDER,
                                          packages=params.PIP_PACKAGES,
                                          rebuild=False,
                                          quiet=True)
        # Replace process with one invoked in the virtual environment.
        os.execlp(venv_python_path, venv_python_path, *sys.argv)


def virtual_environment_main(params: init_file.ParamData):
    """Run Jiig application, assuming we're inside the virtual environment."""

    venv_python_path = os.path.join(params.VENV_FOLDER, 'bin', 'python')
    if sys.executable != venv_python_path:
        utility.abort('Not executing inside the virtual environment.')
    # Main import can not be global, because it depends on virtual environment.
    from .main import main
    main(params)


def initialize_application(jiig_folder: Text):
    """Perform all steps to execute the application."""
    # Load configuration parameters and add any extras.
    app_folder = os.getcwd()
    params = load_configuration([jiig_folder, app_folder])
    params['APP_FOLDER'] = app_folder
    # Re-execute inside the virtual environment or continue.
    virtual_environment_check(params)
    # Inside virtual environment. Parse command line and start app.
    virtual_environment_main(params)
