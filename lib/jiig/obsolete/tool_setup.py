"""
Prepare runtime tool data based on user-specified tool configuration.
"""

import os
import sys

from jiig import config


def initialize(tool_config: config.Tool):
    """
    Prepare ToolData from configured Tool.

    :param tool_config: tool configuration object
    """
    # Add tool and Jiig library folders to interpreter load path.
    for lib_folder in reversed(tool_config.get_library_folders()):
        if os.path.isdir(lib_folder) and lib_folder not in sys.path:
            sys.path.insert(0, lib_folder)
