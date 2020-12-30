"""
Option flags shared by CLI parsers.
"""

from typing import Text

VERBOSE = False
DEBUG = False
DRY_RUN = False

TOP_COMMAND_LABEL = 'COMMAND'
SUB_COMMAND_LABEL = 'SUB_COMMAND'


# For now, only argparse is supported.
# Hoping to provide an argparse alternative in the future.
class ParserImplementations:
    argparse = 'argparse'


DEFAULT_IMPLEMENTATION = ParserImplementations.argparse


# noinspection DuplicatedCode
def set_options(verbose: bool = None,
                debug: bool = None,
                dry_run: bool = None,
                default_implementation: Text = None,
                top_command_label: Text = None,
                sub_command_label: Text = None,
                ):
    global VERBOSE, DEBUG, DRY_RUN, DEFAULT_IMPLEMENTATION, TOP_COMMAND_LABEL, SUB_COMMAND_LABEL
    if verbose is not None:
        VERBOSE = verbose
    if debug is not None:
        DEBUG = debug
    if dry_run is not None:
        DRY_RUN = dry_run
    if default_implementation is not None:
        DEFAULT_IMPLEMENTATION = default_implementation
    if top_command_label is not None:
        TOP_COMMAND_LABEL = top_command_label
    if sub_command_label is not None:
        SUB_COMMAND_LABEL = sub_command_label
