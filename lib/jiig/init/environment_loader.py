"""
Python interpreter initialization.
"""

import os
import sys

from jiig import cli, const, model, util

from .cli_preprocessor import CLIPreParseData


def initialize(bootstrap: model.ToolBootstrap,
               pre_parse_data: CLIPreParseData,
               ):
    """
    Initialize runtime environment.

    Update the Python interpreter library path.

    :param bootstrap: tool bootstrap object
    :param pre_parse_data: preliminary CLI parsing results with global options, etc.
    """
    # Push options into libraries to keep a one-way dependency from Jiig to
    # independent libraries, without needing a back-channel for options.
    util.set_options(verbose=pre_parse_data.verbose,
                     debug=pre_parse_data.debug,
                     dry_run=pre_parse_data.dry_run)
    cli.set_options(verbose=pre_parse_data.verbose,
                    debug=pre_parse_data.debug,
                    dry_run=pre_parse_data.dry_run,
                    top_command_label=const.TOP_TASK_LABEL,
                    sub_command_label=const.SUB_TASK_LABEL)
    # Add tool and Jiig library folders.
    for lib_folder in reversed(bootstrap.library_folders):
        if os.path.isdir(lib_folder) and lib_folder not in sys.path:
            sys.path.insert(0, lib_folder)
