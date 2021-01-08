"""
On-demand virtual environment loader.

A virtual environment is loaded when the support is enabled, and if it is
flagged as optional, if the active task requires it for non-standard packages.
"""

import os
import sys

from jiig.constants import VENV_DISABLED, VENV_REQUIRED
from jiig.registration.registered_tools import RegisteredTool
from jiig.utility.console import log_message
from jiig.utility.python import build_virtual_environment

from .execution_data import ExecutionData
from .cli_processor import CLIResults


def initialize(exec_data: ExecutionData,
               registered_tool: RegisteredTool,
               parse_results: CLIResults,
               ):
    # Nothing to do if one of the following conditions are met...
    # The virtual environment is disabled.
    if registered_tool.options.venv_support == VENV_DISABLED:
        return
    # The virtual environment is optional and no Pip packages are required.
    if registered_tool.options.venv_support != VENV_REQUIRED:
        if not parse_results.pip_packages:
            return
    # Already running inside the virtual environment.
    venv_interpreter = os.path.join(registered_tool.options.venv_folder, 'bin', 'python')
    if sys.executable == venv_interpreter:
        return
    # Build the virtual environment as needed.
    build_virtual_environment(registered_tool.options.venv_folder,
                              packages=parse_results.pip_packages,
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
    # Does not return.
