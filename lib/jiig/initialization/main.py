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

from . import cli_preprocessor, environment_loader, tool_loader, cli_processor, \
    virtual_environment_loader, task_loader

from .execution_data import ExecutionData


def main(exec_data: ExecutionData):
    """
    Main function called from jiig-run to drive all stages of tool initialization.

    :param exec_data: script paths and command line arguments data
    """
    # Run tool script to get registered Tool class.
    registered_tool = tool_loader.initialize(exec_data)

    # Pre-process the command line in order to get some global options.
    pre_results = cli_preprocessor.initialize(exec_data, registered_tool)

    # Initialize Python environment and libraries.
    environment_loader.initialize(exec_data, registered_tool, pre_results)

    # Once the registered tool is in hand, the command line parser can be built
    # based on tool/task metadata, and the command line can be parsed.
    parse_results = cli_processor.initialize(exec_data, registered_tool, pre_results)

    # Load a virtual environment, if one is required and not yet loaded.
    # May restart without returning from this call.
    virtual_environment_loader.initialize(exec_data, registered_tool, parse_results)

    # Finally ready to execute the registered tasks stack.
    task_loader.initialize(exec_data, registered_tool, parse_results)
