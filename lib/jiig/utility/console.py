"""Console i/o utilities."""

import sys
import traceback
from typing import Any, Text

from jiig.internal import global_data


def log_message(text: Any, *args, **kwargs):
    """
    Display message line(s) and indented lines for relevant keyword data.

    tag is a special keyword that prefixes all lines in uppercase.
    """

    tag = kwargs.pop('tag', None)
    verbose = kwargs.pop('verbose', None)
    debug = kwargs.pop('debug', None)
    if verbose and not global_data.VERBOSE:
        return
    if debug and not global_data.DEBUG:
        return
    lines = []
    if text:
        if isinstance(text, (list, tuple)):
            lines.extend(text)
        else:
            lines.append(str(text))
    for value in args:
        lines.append('  {}'.format(value))
    for key, value in kwargs.items():
        if isinstance(value, (list, tuple)):
            for idx, sub_value in enumerate(value):
                lines.append('  {}[{}] = {}'.format(key, idx + 1, sub_value))
        else:
            lines.append('  {} = {}'.format(key, value))
    for line in lines:
        if tag:
            print('{}: {}'.format(tag.upper(), line))
        else:
            print(line)


def print_call_stack(skip: int = 0, limit: int = None):
    print('  ::Call Stack::')
    for file, line, function, source in traceback.extract_stack(limit=limit)[:-skip]:
        print('  {}.{}, {}()'.format(file, line, function))


def abort(text: Any, *args, **kwargs):
    """Display, and in the future log, a fatal _error message (to stderr) and quit."""
    skip = kwargs.pop('skip', 0)
    kwargs['tag'] = 'FATAL'
    log_message(text, *args, **kwargs)
    if global_data.DEBUG:
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
