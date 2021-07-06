"""Console i/o utilities."""

import os
import sys
import traceback
from contextlib import contextmanager
from typing import Any, Text, Set, Iterator, List, Sequence, Dict, Tuple, Optional

from .general import format_message_lines, get_exception_stack
from .options import OPTIONS

MESSAGES_ISSUED_ONCE: Set[Text] = set()
LINES_WRITTEN = 0


class LogWriter:
    """Abstract base class for log writers."""

    def write_line(self, text: str, is_error: bool = False, extra_space: bool = False):
        """
        Write a log line.

        :param text: line text
        :param is_error: True if the line represents an error
        :param extra_space: True to add extra space before and after the line
        """
        raise NotImplementedError


class ConsoleLogWriter(LogWriter):
    """Log writer for stdout/stderr."""

    def write_line(self, text: str, is_error: bool = False, extra_space: bool = False):
        """
        Write a log line.

        :param text: line text
        :param is_error: True if the line represents an error
        :param extra_space: True to add extra space before and after the line
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

    :param log_writer: new log writer
    """
    global _LOG_WRITER
    _LOG_WRITER = log_writer


def log_message(text: Any, *args, **kwargs):
    """
    Display message line(s) and indented lines for relevant keyword data.

    Keywords:
       tag                       prefix for all lines displayed in uppercase
       sub_tag                   optional text to enclose in square brackets next to the tag
       verbose                   True if requires VERBOSE mode
       debug                     True if requires DEBUG mode
       issue_once_tag            unique tag to prevent issuing the message more than once
       exception_traceback       dump traceback stack if an exception is being reported
       exception_traceback_skip  number of stack frames to skip
       exec_file_name            file name to replace <string> in exception output for exec'd file
       exclude_exec_frames       exclude exec() (non-source file) frames
    """
    tag = kwargs.pop('tag', None)
    verbose = kwargs.pop('verbose', None)
    debug = kwargs.pop('debug', None)
    issue_once_tag = kwargs.pop('issue_once_tag', None)
    is_error = kwargs.pop('is_error', False)
    exception_traceback = kwargs.pop('exception_traceback', None)
    exception_traceback_skip = kwargs.pop('exception_traceback_skip', None)
    exclude_exec_frames = kwargs.pop('exclude_exec_frames', None)
    exec_file_name = kwargs.pop('exec_file_name', None)
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
                                     exec_file_name=exec_file_name):
        _LOG_WRITER.write_line(line, is_error=is_error)
    has_exception = False
    for value in list(args) + list(kwargs.values()):
        if isinstance(value, Exception):
            has_exception = True
            break
    # Dump a traceback stack if DEBUG and an exception is being reported.
    if has_exception:
        if OPTIONS.debug:
            exc_lines = traceback.format_exc().split(os.linesep)
            if exc_lines:
                log_message('Exception stack:', *exc_lines, tag='DEBUG', is_error=True)
        elif exception_traceback:
            exc_stack = get_exception_stack(skip=exception_traceback_skip,
                                            exclude_exec_frames=exclude_exec_frames,
                                            exec_file_name=exec_file_name)
            if exc_stack.items:
                lines: List[Text] = []
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
        if not OPTIONS.debug:
            if OPTIONS.is_initialized:
                log_message('(enable debug option for more information)', tag=tag)
            else:
                log_message(f'(set JIIG_DEBUG=1 for more information)', tag=tag)


def abort(text: Any, *args, **kwargs):
    """Display, and in the future log, a fatal _error message (to stderr) and quit."""
    skip = kwargs.pop('skip', 0)
    kwargs['tag'] = 'FATAL'
    kwargs['is_error'] = True
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
    """Display, and in the future log, a warning message (to stderr)."""
    kwargs['tag'] = 'WARNING'
    kwargs['is_error'] = True
    log_message(text, *args, **kwargs)


def log_error(text: Any, *args, **kwargs):
    """Display, and in the future log, an _error message (to stderr)."""
    kwargs['tag'] = 'ERROR'
    kwargs['is_error'] = True
    log_message(text, *args, **kwargs)


def log_heading(level: int, heading: Text):
    """Display, and in the future log, a heading message to delineate blocks."""
    decoration = f'=====' if level <= 1 else f'---'
    if heading:
        line = ' '.join([decoration, heading, decoration])
    else:
        line = decoration
    _LOG_WRITER.write_line(line, extra_space=True)


def log_block_begin(level: int, heading: Text):
    """
    Display, and in the future log, a heading message to delineate blocks.

    For now it just calls log_heading().
    """
    log_heading(level, heading)


def log_block_end(level: int):
    """Display, and in the future log, a message to delineate block endings."""
    log_heading(level, '')


class Logger:
    """A pre-configured logger, e.g. to add a sub-tag to every output line."""

    def __init__(self, sub_tag: Text = None):
        """
        Logger constructor.

        :param sub_tag: optional sub-tag to add to tagged lines
        """
        self.sub_tag = sub_tag

    def error(self, text: Any, *args, **kwargs):
        """
        Display an error.

        :param text: message text
        :param args: positional data arguments
        :param kwargs: keywords data arguments
        """
        log_error(text, *args, **kwargs, sub_tag=self.sub_tag)

    def warning(self, text: Any, *args, **kwargs):
        """
        Display a warning.

        :param text: message text
        :param args: positional data arguments
        :param kwargs: keywords data arguments
        """
        log_warning(text, *args, **kwargs, sub_tag=self.sub_tag)

    def message(self, text: Any, *args, **kwargs):
        """
        Display an informational message.

        Checked for uniqueness so that a particular note only appears once.

        :param text: message text
        :param args: positional data arguments
        :param kwargs: keywords data arguments
        """
        log_message(text, *args, **kwargs, sub_tag=self.sub_tag)

    def abort(self, text: Any, *args, **kwargs):
        """
        Display a fatal error and exit.

        :param text: message text
        :param args: positional data arguments
        :param kwargs: keywords data arguments
        """
        abort(text, *args, **kwargs, sub_tag=self.sub_tag)

    @staticmethod
    def heading(level: int, heading: Text):
        """
        Display, and in the future log, a heading message to delineate blocks.

        :param level: heading level, 1-n
        :param heading: heading text
        """
        log_heading(level, heading)

    @staticmethod
    def block_begin(level: int, heading: Text):
        """
        Display, and in the future log, a heading message to delineate blocks.

        For now it just calls log_heading().

        :param level: heading level, 1-n
        :param heading: heading text
        """
        log_block_begin(level, heading)

    @staticmethod
    def block_end(level: int):
        """
        Display, and in the future log, a message to delineate block endings.

        :param level: heading level, 1-n
        """
        log_block_end(level)


class TopicLogger:
    """Topic logger provided by log_topic()."""
    def __init__(self,
                 topic: Text,
                 delayed: bool = None,
                 parent: 'TopicLogger' = None,
                 sub_tag: Text = None):
        """
        Construct a topic or sub-topic.

        :param topic: topic heading text or used as preamble if parent is not None
        :param delayed: collect output and display at the end (inherited by default)
        :param parent: parent TopicLogger, set if it is a sub-topic
        :param sub_tag: optional sub-tag to add to tagged lines
        """
        self._logger = Logger(sub_tag=sub_tag)
        self.topic: Text = topic
        if delayed is None:
            if parent:
                delayed = parent.delayed
            else:
                delayed = False
        self.delayed = delayed
        self.parent: Optional[TopicLogger] = parent
        self.errors: List[Tuple[Any, Sequence, Dict]] = []
        self.warnings: List[Tuple[Any, Sequence, Dict]] = []
        self.messages: List[Tuple[Any, Sequence, Dict]] = []
        self.heading_level = 1
        topic = self
        while topic.parent is not None:
            self.heading_level += 1
            topic = topic.parent
        if not self.delayed:
            self._logger.heading(self.heading_level, self.topic)

    def error(self, text: Any, *args, **kwargs):
        """
        Add an error.

        :param text: message text
        :param args: positional data arguments
        :param kwargs: keywords data arguments
        """
        if self.delayed:
            if self.parent is None:
                self.errors.append((text, args, kwargs))
            else:
                self.parent.error(f'{self.topic}: {text}', *args, **kwargs)
        else:
            self._logger.error(text, *args, **kwargs)

    def warning(self, text: Any, *args, **kwargs):
        """
        Add a warning.

        :param text: message text
        :param args: positional data arguments
        :param kwargs: keywords data arguments
        """
        if self.delayed:
            if self.parent is None:
                self.warnings.append((text, args, kwargs))
            else:
                self.parent.warning(f'{self.topic}: {text}', *args, **kwargs)
        else:
            self._logger.warning(text, *args, **kwargs)

    def message(self, text: Any, *args, **kwargs):
        """
        Add a message.

        Checked for uniqueness so that a particular note only appears once.

        :param text: message text
        :param args: positional data arguments
        :param kwargs: keywords data arguments
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
                  topic: Text,
                  delayed: bool = None,
                  ) -> Iterator['TopicLogger']:
        """
        Context manager to start a sub-topic.

        :param topic: sub-topic heading used as message preamble
        :param delayed: collect output and display at the end (inherited by default)
        :return: sub-TopicLogger to call with sub-topic messages
        """
        sub_topic_logger = TopicLogger(topic, delayed=delayed, parent=self)
        yield sub_topic_logger
        sub_topic_logger.flush()

    def get_counts(self) -> Tuple[int, int, int]:
        """
        Get current error/warning/message counts.

        :return: (error_count, warning_count, message_count) tuple
        """
        return len(self.errors), len(self.warnings), len(self.messages)

    def flush(self):
        """
        Flush messages.

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
def log_topic(topic: Text, delayed: bool = False) -> Iterator[TopicLogger]:
    """
    Provide a context manager to start a topic.

    Topic errors, warnings, and messages are flushed at the end of the `with`
    block invoking this function.

    :param topic: topic heading text
    :param delayed: collect output and display at the end
    :return: TopicLogger that the caller can use to add various message types
    """
    topic_logger = TopicLogger(topic, delayed=delayed)
    yield topic_logger
    topic_logger.flush()
