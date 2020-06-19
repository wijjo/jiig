class Jiig:
    virtual_environment = 'venv'
    configuration_extension = '.yaml'
    local_configuration_suffix = '-local'
    # Command line parsing constants.
    cli_dest_name_prefix = 'TASK'
    cli_dest_name_separator = '.'
    cli_dest_name_preamble = cli_dest_name_prefix + cli_dest_name_separator
    cli_metavar_suffix = 'SUB_TASK'
    cli_metavar_separator = '_'
