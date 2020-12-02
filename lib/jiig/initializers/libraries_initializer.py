"""
Utility library initializations.

Push options into libraries to keep a one-way dependency from Jiig to
independent libraries, without needing a back-channel for options.
"""

from jiig import utility, cli_parsing, registration

from .parameters_initializer import ParameterData


def initialize(param_data: ParameterData):
    utility.set_options(verbose=param_data.verbose,
                        debug=param_data.debug,
                        dry_run=param_data.dry_run)
    cli_parsing.set_options(verbose=param_data.verbose,
                            debug=param_data.debug,
                            dry_run=param_data.dry_run,
                            top_command_label=param_data.top_task_label,
                            sub_command_label=param_data.sub_task_label)
    registration.set_options(verbose=param_data.verbose,
                             debug=param_data.debug,
                             dry_run=param_data.dry_run,
                             full_name_separator=param_data.full_name_separator)
