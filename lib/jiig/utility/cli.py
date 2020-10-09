"""CLI utilities."""

from typing import Text

from jiig.internal import global_data
from .console import log_error


def make_dest_name(*names: Text) -> Text:
    """Produce a dest name based on a name list."""
    prefixed_names = [global_data.cli_dest_name_prefix] + [name.upper() for name in names]
    return global_data.cli_dest_name_separator.join(prefixed_names)


def append_dest_name(dest_name: Text, *names: Text) -> Text:
    """Add to an existing dest name."""
    return global_data.cli_dest_name_separator.join(
        [dest_name] + [name.upper() for name in names])


def make_metavar(*names: Text) -> Text:
    """Produce a metavar name based on a name list."""
    suffixed_names = [name.upper() for name in names] + [global_data.cli_metavar_suffix]
    return global_data.cli_metavar_separator.join(suffixed_names)


def metavar_to_dest_name(metavar: Text) -> Text:
    if metavar.endswith(global_data.cli_metavar_suffix):
        prepped_name = metavar[:-(len(global_data.cli_metavar_suffix) + 1)].lower()
        names = prepped_name.split(global_data.cli_metavar_separator)
        return make_dest_name(*names)
    log_error(f'metavar_to_dest_name: bad metavar name: {metavar}')
    return ''
