"""Console i/o utilities."""

import sys
import traceback
from typing import Any, Text, Set

from .general import format_message_lines
from . import options

MESSAGES_ISSUED_ONCE: Set[Text] = set()


def log_message(text: Any, *args, **kwargs):
    """
    Display message line(s) and indented lines for relevant keyword data.

    Keywords:
       tag             prefix for all lines displayed in uppercase
       verbose         True if requires VERBOSE mode
       debug           True if requires DEBUG mode
       issue_once_tag  unique tag to prevent issuing the message more than once
    """
    verbose = kwargs.pop('verbose', None)
    debug = kwargs.pop('debug', None)
    issue_once_tag = kwargs.pop('issue_once_tag', None)
    if verbose and not options.VERBOSE:
        return
    if debug and not options.DEBUG:
        return
    if issue_once_tag:
        if issue_once_tag in MESSAGES_ISSUED_ONCE:
            return
        MESSAGES_ISSUED_ONCE.add(issue_once_tag)
    for line in format_message_lines(text, *args, **kwargs):
        print(line)


def print_call_stack(skip: int = None,
                     limit: int = None,
                     tb: object = None,
                     label: Text = None):
    print(f'  ::{label or "Call"} Stack::')
    if tb:
        stack = traceback.extract_tb(tb, limit=limit)
    else:
        stack = traceback.extract_stack(limit=limit)
    if skip is not None:
        stack = stack[:-skip]
    for file, line, function, source in stack:
        print('  {}.{}, {}()'.format(file, line, function))


def abort(text: Any, *args, **kwargs):
    """Display, and in the future log, a fatal _error message (to stderr) and quit."""
    skip = kwargs.pop('skip', 0)
    kwargs['tag'] = 'FATAL'
    log_message(text, *args, **kwargs)
    if options.DEBUG:
        print_call_stack(skip=skip + 2)
    sys.exit(255)


def log_warning(text: Any, *args, **kwargs):
    """Display, and in the future log, a warning message (to stderr)."""
    kwargs['tag'] = 'WARNING'
    log_message(text, *args, **kwargs)


def log_error(text: Any, *args, **kwargs):
    """Display, and in the future log, an _error message (to stderr)."""
    kwargs['tag'] = 'ERROR'
    log_message(text, *args, **kwargs)


def log_heading(level: int, heading: Text):
    """Display, and in the future log, a heading message to delineate blocks."""
    decoration = '=====' if level == 1 else '---'
    print(f'{decoration} {heading} {decoration}')
