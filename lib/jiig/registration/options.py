"""
Option flags for tool/task registration.
"""

from typing import Text

VERBOSE = False
DEBUG = False
DRY_RUN = False

# Package-global setting: Separator for concatenating full task names,
# initialized through api.set_options().
FULL_NAME_SEPARATOR = '(no separator)'


def set_options(verbose: bool = None,
                debug: bool = None,
                dry_run: bool = None,
                full_name_separator: Text = None,
                ):
    global VERBOSE, DEBUG, DRY_RUN, FULL_NAME_SEPARATOR
    if verbose is not None:
        VERBOSE = verbose
    if debug is not None:
        DEBUG = debug
    if dry_run is not None:
        DRY_RUN = dry_run
    if full_name_separator is not None:
        FULL_NAME_SEPARATOR = full_name_separator
