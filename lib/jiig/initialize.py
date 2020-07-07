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
from typing import Text, Set, List

from . import constants, init_file, utility

INIT_PARAM_TYPES = [
    init_file.ParamString('TOOL_NAME'),
    init_file.ParamString('TOOL_DESCRIPTION', default_value='(no description provided)'),
    init_file.ParamFolder('BASE_FOLDER'),
    init_file.ParamFolder('VENV_ROOT'),
    init_file.ParamFolderList('LIB_FOLDERS'),
    init_file.ParamList('PIP_PACKAGES', unique=True, default_value=[]),
]


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


class InitFileFinder:

    def __init__(self):
        self.folder_real_paths: Set[Text] = set()
        self.init_paths: List[Text] = []

    def add_folder(self, folder: Text):
        if folder:
            folder_real_path = os.path.realpath(folder)
            if folder_real_path not in self.folder_real_paths:
                init_path = os.path.join(folder, constants.INIT_FILE)
                if os.path.isfile(init_path):
                    self.init_paths.append(init_path)
                    self.folder_real_paths.add(folder_real_path)


def initialize_tool(tool_root: Text = None):
    """Perform all steps to execute the application."""
    # If running a *IX system-installed copy, find the init file in a parallel etc folder.
    init_file_finder = InitFileFinder()
    my_folder = os.path.dirname(os.path.realpath(__file__))
    if os.path.sep == '/' and my_folder.startswith('/'):
        init_file_finder.add_folder('/usr/local/etc/jiig')
        init_file_finder.add_folder('/etc/jiig')
    jiig_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if not init_file_finder.init_paths:
        init_file_finder.add_folder(jiig_root)
    if not init_file_finder.init_paths:
        utility.abort(f'Jiig init file, "{constants.INIT_FILE}", not found.')
    init_file_finder.add_folder(tool_root)
    init_file_finder.add_folder(os.getcwd())
    all_params = init_file.load_files(INIT_PARAM_TYPES, *init_file_finder.init_paths)
    all_params['JIIG_ROOT'] = jiig_root
    # Isolate the tool's own parameters to handle things like checking if a
    # non-inheritable task should be included. Will receive a None value for
    # tool_root when running the `jiig` command instead of the tool script.
    # Use the first init path for `jiig` script or the last path for the tool.
    if tool_root:
        tool_init_path = init_file_finder.init_paths[-1]
    else:
        tool_init_path = init_file_finder.init_paths[0]
    tool_params = init_file.load_files(INIT_PARAM_TYPES, tool_init_path)
    if all_params.VENV_ROOT:
        # Re-execute inside the virtual environment or continue.
        virtual_environment_check(all_params)
        # Should not get here if not in the virtual environment.
        venv_python_path = os.path.join(all_params.VENV_ROOT, 'bin', 'python')
        if sys.executable != venv_python_path:
            utility.abort('Not executing inside the expected virtual environment.')
    # Main import can not be global, because it depends on virtual environment.
    from .main import main
    main(all_params, tool_params)
