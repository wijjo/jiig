"""
Option flags shared by utilities.
"""

VERBOSE = False
DEBUG = False
DRY_RUN = False


def set_options(verbose: bool = None,
                debug: bool = None,
                dry_run: bool = None,
                ):
    global VERBOSE, DEBUG, DRY_RUN
    if verbose is not None:
        VERBOSE = verbose
    if debug is not None:
        DEBUG = debug
    if dry_run is not None:
        DRY_RUN = dry_run
