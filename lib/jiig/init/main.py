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

import sys
from typing import List, Text

from jiig import model

from . import \
    cli_preprocessor, \
    cli_processor, \
    environment_loader, \
    task_runner, \
    tool_booter, \
    venv_loader


def main(bootstrap: model.ToolBootstrap,
         runner_args: List[Text] = None,
         cli_args: List[Text] = None,
         ):
    """
    Main function called from jiig-run to drive all stages of tool initialization.

    :param bootstrap: tool bootstrap object
    :param runner_args: optional runner, e.g. jiig-run, preamble
    :param cli_args: command line arguments to override the default, sys.argv[1:]
    """
    if cli_args is None:
        cli_args = sys.argv[1:]

    # Pre-process the command line in order to get some global options.
    pre_parse_data = cli_preprocessor.initialize(bootstrap, cli_args)

    # Initialize Python environment and libraries.
    environment_loader.initialize(bootstrap, pre_parse_data)

    # Load a virtual environment, if one is required and not yet loaded.
    # May restart without returning from this call.
    venv_loader.initialize(bootstrap, runner_args, cli_args, pre_parse_data)

    # Boot the tool.
    registered_tool = tool_booter.initialize(bootstrap)

    # Given the registered tool, a command line parser can be constructed based
    # on tool/task metadata, and the command line can be parsed.
    parse_data = cli_processor.initialize(bootstrap, registered_tool, pre_parse_data)

    # Finally ready to execute the registered tasks stack.
    task_runner.initialize(cli_args, registered_tool, parse_data)
