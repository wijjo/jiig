# Copyright (C) 2020-2022, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

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

from .tool import Tool


def main(tool: Tool,
         runner_args: list[str] = None,
         cli_args: list[str] = None,
         ):
    """
    Main function called from jiig script to drive tool and task initialization.

    :param tool: registered user-supplied raw tool configuration object
    :param runner_args: optional Jiig runner preamble, e.g. for jiig shebang usage
    :param cli_args: command line arguments to override the default, sys.argv[1:]
    """
    # Hide internal dependencies to all importing by the root package.
    from .internal.configuration.tool import ToolConfiguration
    from .internal.execution.arguments import RuntimeArguments
    from .internal.execution.runner import Runner
    from .internal.preparation.application import PreparedApplication
    from .internal.preparation.driver import PreparedDriver
    from .internal.preparation.interpreter import prepare_interpreter
    from .internal.preparation.runtime import PreparedRuntime

    runtime_args = RuntimeArguments.prepare(runner_args, cli_args)

    # Convert user-supplied raw tool configuration to runtime tool configuration.
    tool_config = ToolConfiguration.prepare(tool)

    # Prepare the driver.
    prepared_driver = PreparedDriver.prepare(tool_config,
                                             runtime_args.driver)

    # Prepare interpreter. Check for a required virtual environment and restart
    # as needed to run inside the virtual environment.
    prepare_interpreter(tool_config,
                        runtime_args.runner,
                        runtime_args.cli)

    # Prepare application tasks.
    prepared_application = PreparedApplication.prepare(tool_config,
                                                       prepared_driver)

    # Create runtime object that is passed to task functions.
    prepared_runtime = PreparedRuntime.prepare(tool_config,
                                               prepared_driver,
                                               prepared_application)

    # Use the Runner object to run the application.
    runner = Runner(prepared_application, prepared_runtime)
    runner.run_application()
