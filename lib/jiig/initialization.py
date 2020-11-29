"""
Jiig main function to boot the tool.

Consists of a series of function calls into the initialization package.

The `initializers` package modules each provide an `initialize()` function. The
`initialize()` function receives previously-loaded data, which it massages, as
needed, and applies to tool state, as appropriate.

Note that by convention `initializers` modules are either read-only or
write-only. Read-only modules are kept side-effect-free and return loaded data.
Write-only modules return no data.
"""

import os
import sys

from jiig.initializers import parameters_initializer, libraries_initializer, \
    interpreter_initializer, tool_initializer, arguments_initializer, runner_initializer


def initialize():
    """Main function called from jiig-run to drive all stages of tool initialization."""

    if len(sys.argv) < 2 or not os.path.isfile(sys.argv[1]):
        sys.stderr.write(f'FATAL: jiig-run should not be run directly.{os.linesep}')
        sys.exit(1)

    # Load run parameters from globals, command line, and tool initialization file.
    param_data = parameters_initializer.initialize(command_line_arguments=sys.argv)

    # Apply parameters to utility libraries, as appropriate.
    libraries_initializer.initialize(param_data)

    # Initialize Python environment (may restart and not return).
    interpreter_initializer.initialize(param_data)

    # Run the tool script to let it register tasks, etc..
    tool_data = tool_initializer.initialize(param_data)

    # Parse command line based on the tool/task registry data.
    arg_data = arguments_initializer.initialize(param_data, tool_data)

    # Execute the tool.
    runner_initializer.initialize(param_data, tool_data, arg_data)
