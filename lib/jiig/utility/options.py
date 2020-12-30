"""
Option flags shared by utilities.
"""

VERBOSE = False
DEBUG = False
DRY_RUN = False
MESSAGE_INDENT = '   '
COLUMN_SEPARATOR = '  '


# noinspection DuplicatedCode
def set_options(verbose: bool = None,
                debug: bool = None,
                dry_run: bool = None,
                message_indent: str = None,
                column_separator: str = None,
                ):
    global VERBOSE, DEBUG, DRY_RUN, MESSAGE_INDENT, COLUMN_SEPARATOR
    if verbose is not None:
        VERBOSE = verbose
    if debug is not None:
        DEBUG = debug
    if dry_run is not None:
        DRY_RUN = dry_run
    if message_indent is not None:
        MESSAGE_INDENT = message_indent
    if column_separator is not None:
        COLUMN_SEPARATOR = column_separator
