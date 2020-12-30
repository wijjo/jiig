"""
Load and initialize tool and tool help.
"""

import os
import sys
import traceback
from typing import Type

from jiig.constants import TOOL_MODULE_CLASS_NAME
from jiig.registration.tools import Tool
from jiig.registration.registered_tools import RegisteredTool
from jiig.utility.console import abort
from jiig.utility.general import format_message_lines
from jiig.utility.stream import open_text_source

from .execution_data import ExecutionData


def initialize(exec_data: ExecutionData) -> RegisteredTool:
    """
    Load the tool script and provide the registered tool.

    :param exec_data: script paths and command line arguments data
    """
    # Add the Jiig library path if missing.
    if exec_data.jiig_library_path not in sys.path:
        sys.path.insert(0, exec_data.jiig_library_path)
    # Add tool library folders.
    tool_lib_path = os.path.join(
        os.path.dirname(os.path.realpath(exec_data.tool_script_path)),
        'lib')
    if os.path.isdir(tool_lib_path) and tool_lib_path not in sys.path:
        sys.path.insert(0, tool_lib_path)

    fake_module_symbols = {}
    try:
        with open_text_source(file=exec_data.tool_script_path) as text_stream:
            exec(text_stream.read(), fake_module_symbols)
        if TOOL_MODULE_CLASS_NAME not in fake_module_symbols:
            abort(f'Tool class "{TOOL_MODULE_CLASS_NAME}" not found in tool script.',
                  exec_data.tool_script_path)
        tool_class: Type[Tool] = fake_module_symbols[TOOL_MODULE_CLASS_NAME]
        if not issubclass(tool_class, Tool):
            abort(f'Class "{TOOL_MODULE_CLASS_NAME}" is not a Tool sub-class.',
                  exec_data.tool_script_path)
        if tool_class.name is None:
            tool_class.name = os.path.basename(exec_data.tool_script_path)
        return RegisteredTool(tool_class)
    except Exception as exc:
        from jiig.utility.console import log_error
        for line in format_message_lines('Failed to load tool script and tool class.',
                                         exec_data.tool_script_path,
                                         str(exc),
                                         tag='FATAL'):
            sys.stderr.write(line)
            sys.stderr.write(os.linesep)
        traceback_lines = traceback.format_exc().split(os.linesep)[3:]
        traceback_lines[0] = traceback_lines[0].replace(
            '<string>', exec_data.tool_script_path).replace(
            ', in <module>', '')
        for line in traceback_lines:
            sys.stderr.write(line)
            sys.stderr.write(os.linesep)
        sys.exit(255)
