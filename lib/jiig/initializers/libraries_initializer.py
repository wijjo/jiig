"""
Utility library initializations.
"""

from jiig import utility, cli_parse, registry

from .parameters_initializer import ParameterData


def initialize(param_data: ParameterData):
    utility.set_options(verbose=param_data.verbose,
                        debug=param_data.debug,
                        dry_run=param_data.dry_run)
    cli_parse.set_options(verbose=param_data.verbose,
                          debug=param_data.debug,
                          dry_run=param_data.dry_run,
                          top_command_label=param_data.top_task_label,
                          sub_command_label=param_data.sub_task_label)
    registry.set_options(full_name_separator=param_data.full_name_separator)
