"""Console i/o utilities."""

import os
import sys
import traceback
from contextlib import contextmanager
from typing import Any, Text, Set, Iterator, List, Sequence, Dict, Tuple, Optional

from . import options
from .general import format_message_lines, fit_text

MESSAGES_ISSUED_ONCE: Set[Text] = set()


def log_message(text: Any, *args, **kwargs):
    """
    Display message line(s) and indented lines for relevant keyword data.

    Keywords:
       tag                  prefix for all lines displayed in uppercase
       sub_tag              optional text to enclose in square brackets next to the tag
       verbose              True if requires VERBOSE mode
       debug                True if requires DEBUG mode
       issue_once_tag       unique tag to prevent issuing the message more than once
       exception_traceback  dump traceback stack if an exception is being reported
    """
    verbose = kwargs.pop('verbose', None)
    debug = kwargs.pop('debug', None)
    issue_once_tag = kwargs.pop('issue_once_tag', None)
    stream = kwargs.pop('log_stream', sys.stdout)
    exception_traceback = kwargs.pop('exception_traceback', None)
    if verbose and not options.VERBOSE:
        return
    if debug and not options.DEBUG:
        return
    if issue_once_tag:
        if issue_once_tag in MESSAGES_ISSUED_ONCE:
            return
        MESSAGES_ISSUED_ONCE.add(issue_once_tag)
    for line in format_message_lines(text, *args, **kwargs):
        stream.write(line)
        stream.write(os.linesep)
    # Dump a traceback stack if DEBUG and an exception is being reported.
    if options.DEBUG:
        for value in list(args) + list(kwargs.values()):
            if isinstance(value, Exception):
                traceback.print_exc()
                break
    elif exception_traceback:
        lines: List[Text] = []
        last_exc_tb = sys.exc_info()[2]
        if last_exc_tb is not None:
            for tb in reversed(traceback.extract_tb(last_exc_tb)):
                if not os.path.exists(tb.filename):
                    break
                location = '.'.join([tb.filename, str(tb.lineno)])
                lines.append(f'{fit_text(location, 32, front=True, pad=" ")}: {tb.line}')
            if lines:
                log_error('Exception stack:', *reversed(lines))


def abort(text: Any, *args, **kwargs):
    """Display, and in the future log, a fatal _error message (to stderr) and quit."""
    from . import options
    skip = kwargs.pop('skip', 0)
    kwargs['tag'] = 'FATAL'
    kwargs['log_stream'] = sys.stderr
    kwargs['exception_traceback'] = True
    # kwargs['exception_traceback'] = True
    log_message(text, *args, **kwargs)
    # If DEBUG is enabled dump a call stack and strip off the non-meaningful tail.
    if options.DEBUG:
        traceback_lines = traceback.format_stack()[:-(skip + 1)]
        for line in traceback_lines:
            sys.stderr.write(line)
    sys.exit(255)


def log_warning(text: Any, *args, **kwargs):
    """Display, and in the future log, a warning message (to stderr)."""
    kwargs['tag'] = 'WARNING'
    kwargs['log_stream'] = sys.stderr
    log_message(text, *args, **kwargs)


def log_error(text: Any, *args, **kwargs):
    """Display, and in the future log, an _error message (to stderr)."""
    kwargs['tag'] = 'ERROR'
    kwargs['log_stream'] = sys.stderr
    log_message(text, *args, **kwargs)


def log_heading(level: int, heading: Text):
    """Display, and in the future log, a heading message to delineate blocks."""
    decoration = '=====' if level == 1 else '---'
    sys.stdout.write(f'{decoration} {heading} {decoration}{os.linesep}')


def log_block_begin(level: int, heading: Text):
    """
    Display, and in the future log, a heading message to delineate blocks.

    For now it just calls log_heading().
    """
    log_heading(level, heading)


def log_block_end(level: int):
    """Display, and in the future log, a message to delineate block endings."""
    decoration = '=====' if level == 1 else '---'
    sys.stdout.write(f'{decoration}{os.linesep}')


class TopicLogger:
    """Topic logger provided by log_topic()."""
    def __init__(self,
                 topic: Text,
                 delayed: bool = None,
                 parent: 'TopicLogger' = None):
        """
        Construct a topic or sub-topic.

        :param topic: topic heading text or used as preamble if parent is not None
        :param delayed: collect output and display at the end (inherited by default)
        :param parent: parent TopicLogger, set if it is a sub-topic
        """
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
            log_heading(self.heading_level, self.topic)

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
            log_error(text, *args, **kwargs)

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
            log_warning(text, *args, **kwargs)

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
            log_message(text, *args, **kwargs)

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
                log_block_begin(self.heading_level, self.topic)
                for text, args, kwargs in self.errors:
                    log_error(text, *args, **kwargs)
                self.errors = []
                for text, args, kwargs in self.warnings:
                    log_warning(text, *args, **kwargs)
                self.warnings = []
                for text, args, kwargs in self.messages:
                    log_message(text, *args, **kwargs)
                self.messages = []
                if self.heading_level == 1:
                    log_block_end(self.heading_level)
        else:
            if self.heading_level == 1:
                log_block_end(self.heading_level)


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
