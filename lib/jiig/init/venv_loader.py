"""
On-demand virtual environment loader.

A virtual environment is loaded when the support is enabled, and if it is
flagged as optional, if the active task requires it for non-standard packages.
"""

import os
import sys
from typing import Text, List, Optional

from jiig import model
from jiig.util.console import log_message
from jiig.util.python import build_virtual_environment

from .cli_preprocessor import CLIPreParseData


def initialize(bootstrap: model.ToolBootstrap,
               runner_args: Optional[List[Text]],
               cli_args: Optional[List[Text]],
               _pre_parse_data: CLIPreParseData,
               ):
    """
    Check if a virtual environment is required and restart inside it as needed.

    Update the Python interpreter library path.

    Will not return if it needs to restart in the virtual environment.

    Note that _pre_parse_data is not currently used, but might become relevant
    in the future, e.g. for debug/verbose-based decision-making.

    :param bootstrap: tool bootstrap object
    :param runner_args: optional runner, e.g. jiig-run, preamble
    :param cli_args: command line arguments to override the default, sys.argv[1:]
    :param _pre_parse_data: preliminary CLI parsing results with global options, etc.
    """
    # Do nothing if a virtual environment is not needed.
    if not bootstrap.pip_packages and not bootstrap.venv_required:
        return

    # Do nothing if already running inside the virtual environment.
    venv_interpreter = os.path.join(bootstrap.venv_folder, 'bin', 'python')
    if sys.executable == venv_interpreter:
        return

    # Build the virtual environment as needed.
    build_virtual_environment(bootstrap.venv_folder,
                              packages=bootstrap.pip_packages,
                              rebuild=False,
                              quiet=True)

    # Restart inside the virtual environment with '--' inserted to help parsing.
    args = [venv_interpreter]
    if runner_args is not None:
        args.extend(runner_args)
    args.append('--')
    args.extend(cli_args)
    log_message('Re-running inside virtual environment...', verbose=True)
    os.execl(args[0], *args)
    # Does not return.
