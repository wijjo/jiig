"""
Python interpreter initialization.
"""

import os
import sys

from jiig import utility, cli_parsing
from jiig.constants import TOP_TASK_LABEL, SUB_TASK_LABEL
from ..registration.registered_tools import RegisteredTool
from jiig.utility.console import log_message
from jiig.utility.python import build_virtual_environment

from .cli_preprocessor import CLIPreResults
from .execution_data import ExecutionData


def initialize(exec_data: ExecutionData,
               registered_tool: RegisteredTool,
               pre_results: CLIPreResults):
    """
    Check if a virtual environment is required and restart inside it as needed.

    Update the Python interpreter library path.

    Will not return if it needs to restart in the virtual environment.

    :param exec_data: script paths and command line arguments data
    :param registered_tool: registered tool
    :param pre_results: preliminary CLI parsing results with global options, etc.
    """
    # Push options into libraries to keep a one-way dependency from Jiig to
    # independent libraries, without needing a back-channel for options.
    utility.set_options(verbose=pre_results.verbose,
                        debug=pre_results.debug,
                        dry_run=pre_results.dry_run)
    cli_parsing.set_options(verbose=pre_results.verbose,
                            debug=pre_results.debug,
                            dry_run=pre_results.dry_run,
                            top_command_label=TOP_TASK_LABEL,
                            sub_command_label=SUB_TASK_LABEL)
    # Check if it needs to restart inside a virtual environment.
    if registered_tool.options.venv_enabled:
        venv_interpreter = os.path.join(registered_tool.options.venv_folder, 'bin', 'python')
        if sys.executable != venv_interpreter:
            # Build the virtual environment as needed.
            build_virtual_environment(registered_tool.options.venv_folder,
                                      packages=registered_tool.options.pip_packages,
                                      rebuild=False,
                                      quiet=True)
            # Restart inside the virtual environment with '--' inserted to help parsing.
            log_message('Re-running inside virtual environment...', verbose=True)
            os.execl(venv_interpreter,
                     venv_interpreter,
                     exec_data.run_script_path,
                     exec_data.tool_script_path,
                     '--',
                     *exec_data.cli_args)
    # Add tool library folders.
    for lib_folder in reversed(registered_tool.options.library_folders):
        if os.path.isdir(lib_folder) and lib_folder not in sys.path:
            sys.path.insert(0, lib_folder)
    # The automatically-added Jiig root path (added due to this script) is not used, so lose it.
    if exec_data.jiig_root in sys.path:
        sys.path.remove(exec_data.jiig_root)
