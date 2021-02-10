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

from typing import List, Text

from jiig import model
from jiig.util.console import log_message

from . import pre_load, load_tool, prepare_interpreter, load_application, execute_application


def main(tool_config: model.Tool,
         runner_args: List[Text] = None,
         cli_args: List[Text] = None,
         ):
    """
    Main function called from jiig-run to drive tool and task initialization.

    :param tool_config: tool configuration object
    :param runner_args: optional runner, e.g. jiig-run, preamble
    :param cli_args: command line arguments to override the default, sys.argv[1:]
    """
    # Pre-parse global options so that debug/verbose options can apply early.
    pre_load_data = pre_load.go(tool_config, runner_args, cli_args)
    log_message('Pre-loaded global options.', debug=True)

    # Wrap the tool configuration so that all necessary tool data is resolved.
    tool = load_tool.go(tool_config)
    log_message('Prepared tool runtime object.', debug=True)

    # Restart in venv as needed and initialize library load path.
    prepare_interpreter.go(pre_load_data, tool)
    log_message('Prepared Python interpreter environment.', debug=True)

    # Parse CLI arguments based on configured tool and tasks.
    # Produces CLI parameter data, an active task stack
    application_data = load_application.go(pre_load_data, tool)
    log_message('Prepared application for execution.', debug=True)

    # Finally, execute the application task stack.
    execute_application.go(application_data)
