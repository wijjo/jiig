# Copyright (C) 2020-2023, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

"""Console i/o utilities."""

import os
import sys
import traceback
from contextlib import (
    AbstractContextManager,
    contextmanager,
)
from typing import (
    Any,
    Self,
    Sequence,
)

from jiig.constants import CLI_OPTIONS_DEBUG

from .options import OPTIONS
from .exceptions import get_exception_stack
from .messages import format_message_lines

MESSAGES_ISSUED_ONCE: set[str] = set()
LINES_WRITTEN = 0
EXCEPTION_COUNT = 0

DEBUG_INFO_TEXT = f'''
---
For additional termination information try one of the following:
- Specify DEBUG command line option: {' or '.join(CLI_OPTIONS_DEBUG)}
- Set environment variable: JIIG_DEBUG=1
'''.strip()


class LogWriter:
    """Abstract base class for log writers."""

    def write_line(self, text: str, is_error: bool = False, extra_space: bool = False):
        """Write a log line.

        Args:
            text: line text
            is_error: True if the line represents an error
            extra_space: True to add extra space before and after the line
        """
        raise NotImplementedError


class ConsoleLogWriter(LogWriter):
    """Log writer for stdout/stderr."""

    def write_line(self, text: str, is_error: bool = False, extra_space: bool = False):
        """Write a log line.

        Args:
            text: line text
            is_error: True if the line represents an error
            extra_space: True to add extra space before and after the line
        """
        stream = sys.stderr if is_error else sys.stdout
        global LINES_WRITTEN
        if extra_space:
            if LINES_WRITTEN > 0:
                stream.write(os.linesep)
        else:
            LINES_WRITTEN += 1
        stream.write(text)
        stream.write(os.linesep)
        if extra_space:
            stream.write(os.linesep)
            LINES_WRITTEN = 0


# Default to console log writer.
_LOG_WRITER = ConsoleLogWriter()


def set_log_writer(log_writer: LogWriter):
    """
    Establish a new log writer.

    Args:
        log_writer: new log writer
    """
    global _LOG_WRITER
    _LOG_WRITER = log_writer


def log_message(text: Any, *args, **kwargs):
    """Display message line(s) and indented lines for relevant keyword data.

    Special keywords:
       tag                        prefix for all lines displayed in uppercase
       sub_tag                    optional text to enclose in square brackets next to the tag
       verbose                    True if requires VERBOSE mode
       debug                      True if requires DEBUG mode
       is_error                   handle as an error, e.g. by using stderr instead of stdout
       is_fatal                   handle as a fatal error that exits
       issue_once_tag             unique tag to prevent issuing the message more than once
       exception_traceback        dump traceback stack if an exception is being reported
       exception_traceback_skip   number of stack frames to skip
       string_file_name           file name to replace <string> in exception output for exec'd file
       skip_non_source_frames     exclude non-source file frames if True

    Args:
        text: message(s) (can be sequence)
        *args: logged positional arguments
        **kwargs: logged keyword arguments + special keywords
    """
    tag = kwargs.pop('tag', None)
    verbose = kwargs.pop('verbose', None)
    debug = kwargs.pop('debug', None)
    is_error = kwargs.pop('is_error', False)
    is_fatal = kwargs.pop('is_fatal', False)
    issue_once_tag = kwargs.pop('issue_once_tag', None)
    exception_traceback = kwargs.pop('exception_traceback', None)
    exception_traceback_skip = kwargs.pop('exception_traceback_skip', None)
    skip_non_source_frames = kwargs.pop('skip_non_source_frames', None)
    string_file_name = kwargs.pop('string_file_name', None)
    if verbose and not OPTIONS.verbose:
        return
    if debug and not OPTIONS.debug:
        return
    if issue_once_tag:
        if issue_once_tag in MESSAGES_ISSUED_ONCE:
            return
        MESSAGES_ISSUED_ONCE.add(issue_once_tag)
    for line in format_message_lines(text, *args, **kwargs,
                                     tag=tag,
                                     string_file_name=string_file_name):
        _LOG_WRITER.write_line(line, is_error=is_error)
    has_exception = False
    for value in list(args) + list(kwargs.values()):
        if isinstance(value, Exception):
            has_exception = True
            break
    # Dump a traceback stack if DEBUG and an exception is being reported.
    global EXCEPTION_COUNT
    if has_exception:
        EXCEPTION_COUNT += 1
        if OPTIONS.debug:
            exc_lines = traceback.format_exc().split(os.linesep)
            if exc_lines:
                log_message('Exception stack:', *exc_lines, tag='DEBUG', is_error=True)
        elif exception_traceback:
            exc_stack = get_exception_stack(
                skip_frame_count=exception_traceback_skip,
                skip_non_source_frames=skip_non_source_frames,
                string_file_name=string_file_name)
            if exc_stack.items:
                lines: list[str] = []
                if exc_stack.package_path:
                    note = f'(limited to frame: {exc_stack.package_path})'
                    for item in exc_stack.items:
                        sub_path = item.location_string[len(exc_stack.package_path) + 1:]
                        lines.append(f'{sub_path}: {item.text}')
                else:
                    note = ''
                    for item in exc_stack.items:
                        lines.append(f'{item.location_string}: {item.text}')
                if lines:
                    log_message(f'Exception stack{note}:', *lines, tag=tag, is_error=True)
    if not OPTIONS.debug and ((has_exception and EXCEPTION_COUNT == 1) or is_fatal):
        log_message(DEBUG_INFO_TEXT)


def abort(text: Any, *args, **kwargs):
    """Display, and in the future log, a fatal _error message (to stderr) and quit.

    Args:
        text: message(s) (can be sequence)
        *args: logged positional arguments
        **kwargs: logged keyword arguments + special keywords (see
            log_message())
    """
    skip = kwargs.pop('skip', 0)
    kwargs['tag'] = 'FATAL'
    kwargs['is_error'] = True
    kwargs['is_fatal'] = True
    kwargs['exception_traceback'] = True
    log_message(text, *args, **kwargs)
    # If DEBUG is enabled dump a call stack and strip off the non-meaningful tail.
    if OPTIONS.debug:
        traceback_lines = traceback.format_stack()[:-(skip + 1)]
        for traceback_block in traceback_lines:
            for traceback_line in traceback_block.split(os.linesep):
                log_message(traceback_line, tag='DEBUG', is_error=True)
    sys.exit(255)


def log_warning(text: Any, *args, **kwargs):
    """Display, and in the future log, a warning message (to stderr).

    Args:
        text: message(s) (can be sequence)
        *args: logged positional arguments
        **kwargs: logged keyword arguments + special keywords (see
            log_message())
    """
    kwargs['tag'] = 'WARNING'
    kwargs['is_error'] = True
    log_message(text, *args, **kwargs)


def log_error(text: Any, *args, **kwargs):
    """Display, and in the future log, an _error message (to stderr).

    Args:
        text: message(s) (can be sequence)
        *args: logged positional arguments
        **kwargs: logged keyword arguments + special keywords (see
            log_message())
    """
    kwargs['tag'] = 'ERROR'
    kwargs['is_error'] = True
    log_message(text, *args, **kwargs)


def log_heading(heading: str,
                level: int = 0,
                is_error: bool = False,
                compact: bool = False,
                ):
    """Display, and in the future log, a heading message to delineate blocks.

    Args:
        heading: heading text
        level: heading level 0-n
        is_error: log to stderr instead of stdout if True
        compact: omit gap lines if True
    """
    decoration = f'=====' if level <= 1 else f'---'
    if heading:
        line = ' '.join([decoration, heading, decoration])
    else:
        line = decoration
    _LOG_WRITER.write_line(line, extra_space=not compact, is_error=is_error)


def log_block_begin(level: int, heading: str):
    """Display, and in the future log, a heading message to delineate blocks.

    For now it just calls log_heading().

    Args:
        level: block level 0-n
        heading: heading text
    """
    log_heading(heading, level=level)


def log_block_end(level: int):
    """Display, and in the future log, a message to delineate block endings.

    Args:
        level: block level 0-n
    """
    log_heading('', level=level)


class Logger:
    """A pre-configured logger, e.g. to add a sub-tag to every output line."""

    def __init__(self, sub_tag: str = None):
        """Logger constructor.

        Args:
            sub_tag: optional sub-tag to add to tagged lines
        """
        self.sub_tag = sub_tag

    def error(self, text: Any, *args, **kwargs):
        """Display an error.

        Args:
            text: message text
            *args: positional data arguments
            **kwargs: keywords data arguments
        """
        log_error(text, *args, **kwargs, sub_tag=self.sub_tag)

    def warning(self, text: Any, *args, **kwargs):
        """Display a warning.

        Args:
            text: message text
            *args: positional data arguments
            **kwargs: keywords data arguments
        """
        log_warning(text, *args, **kwargs, sub_tag=self.sub_tag)

    def message(self, text: Any, *args, **kwargs):
        """Display an informational message.

        Checked for uniqueness so that a particular note only appears once.

        Args:
            text: message text
            *args: positional data arguments
            **kwargs: keywords data arguments
        """
        log_message(text, *args, **kwargs, sub_tag=self.sub_tag)

    def abort(self, text: Any, *args, **kwargs):
        """Display a fatal error and exit.

        Args:
            text: message text
            *args: positional data arguments
            **kwargs: keywords data arguments
        """
        abort(text, *args, **kwargs, sub_tag=self.sub_tag)

    @staticmethod
    def heading(level: int, heading: str):
        """Display, and in the future log, a heading message to delineate blocks.

        Args:
            level: heading level, 1-n
            heading: heading text
        """
        log_heading(heading, level=level)

    @staticmethod
    def block_begin(level: int, heading: str):
        """Display, and in the future log, a heading message to delineate blocks.

        For now it just calls log_heading().

        Args:
            level: heading level, 1-n
            heading: heading text
        """
        log_block_begin(level, heading)

    @staticmethod
    def block_end(level: int):
        """Display, and in the future log, a message to delineate block endings.

        Args:
            level: heading level, 1-n
        """
        log_block_end(level)


class TopicLogger:
    """Topic logger provided by log_topic()."""
    def __init__(self,
                 topic: str,
                 delayed: bool = None,
                 parent: Self = None,
                 sub_tag: str = None):
        """Construct a topic or sub-topic.

        Args:
            topic: topic heading text or used as preamble if parent is not None
            delayed: collect output and display at the end (inherited by
                default)
            parent: parent TopicLogger, set if it is a sub-topic
            sub_tag: optional sub-tag to add to tagged lines
        """
        self._logger = Logger(sub_tag=sub_tag)
        self.topic: str = topic
        if delayed is not None:
            self.delayed = delayed
        elif parent:
            self.delayed = parent.delayed
        else:
            self.delayed = False
        self.parent: TopicLogger | None = parent
        self.errors: list[tuple[Any, Sequence, dict]] = []
        self.warnings: list[tuple[Any, Sequence, dict]] = []
        self.messages: list[tuple[Any, Sequence, dict]] = []
        self.heading_level = 1
        topic = self
        while topic.parent is not None:
            self.heading_level += 1
            topic = topic.parent
        if not self.delayed:
            self._logger.heading(self.heading_level, self.topic)

    def error(self, text: Any, *args, **kwargs):
        """Add an error.

        Args:
            text: message text
            *args: positional data arguments
            **kwargs: keywords data arguments
        """
        if self.delayed:
            if self.parent is None:
                self.errors.append((text, args, kwargs))
            else:
                self.parent.error(f'{self.topic}: {text}', *args, **kwargs)
        else:
            self._logger.error(text, *args, **kwargs)

    def warning(self, text: Any, *args, **kwargs):
        """Add a warning.

        Args:
            text: message text
            *args: positional data arguments
            **kwargs: keywords data arguments
        """
        if self.delayed:
            if self.parent is None:
                self.warnings.append((text, args, kwargs))
            else:
                self.parent.warning(f'{self.topic}: {text}', *args, **kwargs)
        else:
            self._logger.warning(text, *args, **kwargs)

    def message(self, text: Any, *args, **kwargs):
        """Add a message.

        Checked for uniqueness so that a particular note only appears once.

        Args:
            text: message text
            *args: positional data arguments
            **kwargs: keywords data arguments
        """
        if self.delayed:
            if self.parent is None:
                self.messages.append((text, args, kwargs))
            else:
                self.parent.message(f'{self.topic}: {text}', *args, **kwargs)
        else:
            self._logger.message(text, *args, **kwargs)

    @contextmanager
    def sub_topic(self,
                  topic: str,
                  delayed: bool = None,
                  ) -> AbstractContextManager[Self]:
        """Context manager to start a sub-topic.

        Args:
            topic: sub-topic heading used as message preamble
            delayed: collect output and display at the end (inherited by
                default)

        Returns:
            sub-TopicLogger to call with sub-topic messages
        """
        sub_topic_logger = TopicLogger(topic, delayed=delayed, parent=self)
        yield sub_topic_logger
        sub_topic_logger.flush()

    def get_counts(self) -> tuple[int, int, int]:
        """Get current error/warning/message counts.

        Returns:
            (error_count, warning_count, message_count) tuple
        """
        return len(self.errors), len(self.warnings), len(self.messages)

    def flush(self):
        """Flush messages.

        Generally used only internally, as long as the log_topic()
        contextmanager function and sub_topic() method is used.
        """
        # Note that when self.delayed is False there should be no pending messages.
        if self.delayed:
            if self.errors or self.warnings or self.messages:
                self._logger.block_begin(self.heading_level, self.topic)
                for text, args, kwargs in self.errors:
                    self._logger.error(text, *args, **kwargs)
                self.errors = []
                for text, args, kwargs in self.warnings:
                    self._logger.warning(text, *args, **kwargs)
                self.warnings = []
                for text, args, kwargs in self.messages:
                    self._logger.message(text, *args, **kwargs)
                self.messages = []
                if self.heading_level == 1:
                    self._logger.block_end(self.heading_level)
        else:
            if self.heading_level == 1:
                self._logger.block_end(self.heading_level)


@contextmanager
def log_topic(topic: str,
              delayed: bool = False,
              ) -> AbstractContextManager[TopicLogger]:
    """Provide a context manager to start a topic.

    Topic errors, warnings, and messages are flushed at the end of the `with`
    block invoking this function.

    Args:
        topic: topic heading text
        delayed: collect output and display at the end

    Returns:
        TopicLogger that the caller can use to add various message types
    """
    topic_logger = TopicLogger(topic, delayed=delayed)
    yield topic_logger
    topic_logger.flush()


def display_data(data: Any, heading: str = None):
    """Display data block.

    Args:
        data: data to display
        heading: optional heading text
    """
    sys.stdout.write(os.linesep)
    if heading:
        sys.stdout.write('--- ')
        sys.stdout.write(heading)
    else:
        sys.stdout.write('---')
    sys.stdout.write(os.linesep)
    sys.stdout.write(str(data))
    sys.stdout.write(os.linesep)
    sys.stdout.write('---')
    sys.stdout.write(os.linesep)
