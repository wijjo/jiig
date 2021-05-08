"""
Stream utilities.

For now these are read-only utilities.
"""

import json
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO
from typing import Text, IO, Iterator, Any, Dict, Optional, Callable
from urllib.request import urlopen, Request

from .console import abort, log_error
from .filesystem import get_folder_stack


# noinspection PyBroadException
@dataclass
class _OpenTextResults:
    stream: IO
    source_name: Text


@contextmanager
def _open_text(*,
               text: Text = None,
               file: Text = None,
               stream: IO = None,
               url: Text = None,
               request: Request = None,
               timeout: int = None,
               check: bool = False
               ) -> Iterator[_OpenTextResults]:
    if len([arg for arg in (text, file, stream, url, request)
            if arg is not None]) != 1:
        # In this case we want a call stack from a real exception.
        raise RuntimeError(f'Exactly one of the following keywords is required:'
                           f' text, file, stream, url, or request')
    type_string = None
    try:
        if text is not None:
            text_value = str(text)
            type_string = f'text[{len(text_value)}]'
            yield _OpenTextResults(StringIO(text_value), type_string)
        elif file is not None:
            type_string = f'file["{file}"]'
            with open(file, encoding='utf-8') as file_stream:
                yield _OpenTextResults(file_stream, type_string)
        elif stream is not None:
            type_string = 'stream'
            yield _OpenTextResults(stream, type_string)
        elif url is not None:
            type_string = 'stream'
            with urlopen(url, timeout=timeout) as url_stream:
                yield _OpenTextResults(url_stream, type_string)
        elif request is not None:
            type_string = str(request)
            with urlopen(url, timeout=timeout) as request_stream:
                yield _OpenTextResults(request_stream, type_string)
    except Exception as exc:
        if check:
            abort(f'Failed to open {type_string} in open_text().', exc)
        raise


@contextmanager
def open_text_source(*,
                     text: Text = None,
                     file: Text = None,
                     stream: IO = None,
                     url: Text = None,
                     request: Request = None,
                     timeout: int = None,
                     check: bool = False
                     ) -> Iterator[IO]:
    """
    Open a text source stream for reading.

    It may be a string, file path, stream, URL, or Request object.

    :param text: input string
    :param file: file path
    :param stream: input stream
    :param url: input URL for downloading
    :param request: input Request object for downloading
    :param timeout: timeout in seconds when downloading URL or Request
    :param check: abort cleanly if True, instead of passing along exceptions
    :return: a yielded stream to use in a `with` block for proper closing

    Generates a RuntimeError if one and only one input keyword is not specified.

    Depending on the input type, various kinds of I/O exceptions are possible
    (if checked is False).
    """
    with _open_text(text=text,
                    file=file,
                    stream=stream,
                    url=url,
                    request=request,
                    timeout=timeout,
                    check=check
                    ) as output_data:
        yield output_data.stream


def read_json_source(*,
                     text: Text = None,
                     file: Text = None,
                     stream: IO = None,
                     url: Text = None,
                     request: Request = None,
                     timeout: int = None,
                     check: bool = False
                     ) -> Any:
    """
    Read JSON from a text stream, given a string, file path, stream, URL, or Request object.

    :param text: input string
    :param file: file path
    :param stream: input stream
    :param url: input URL for downloading
    :param request: input Request object for downloading
    :param timeout: timeout in seconds when downloading URL or Request
    :param check: abort cleanly if True, instead of passing along exceptions
    :return: JSON data
    """
    with _open_text(text=text,
                    file=file,
                    stream=stream,
                    url=url,
                    request=request,
                    timeout=timeout,
                    check=check) as output_data:
        try:
            return json.load(output_data.stream)
        except json.JSONDecodeError as exc:
            if check:
                abort(f'Failed to load JSON from {output_data.source_name}.', exc)


def load_json_file_stack(file_name: Text, folder: Text = None) -> Dict:
    """
    Load JSON data from file in folder and containing folders.

    JSON data in each discovered file must be wrapped in a dictionary.

    Traversal is top-down so that data from the closest file takes precedence
    over (and overwrites) data from files that are farther up the stack.

    List elements with common names in multiple files are concatenated.

    Dictionary elements with common names in multiple files are merged.

    Scalar value elements keep only the named value from the closest file.

    :param file_name: file name to look for in each folder of the stack
    :param folder: bottom folder of the search stack, defaults to working folder
    :return: merged data dictionary
    """
    folder_stack = get_folder_stack(os.path.abspath(folder) if folder else os.getcwd())
    data = {}
    for stack_folder in folder_stack:
        path = os.path.join(stack_folder, file_name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as config_file:
                config_data = json.load(config_file)
                if not isinstance(config_data, dict):
                    log_error(f'JSON file "{path}" is not a dictionary.')
                    continue
                for key, value in config_data.items():
                    if key in data:
                        if isinstance(value, list):
                            if isinstance(data[key], list):
                                data[key].extend(value)
                            else:
                                log_error(f'Ignoring non-list value'
                                          f' for "{key}" in "{path}".')
                        elif isinstance(value, dict):
                            if isinstance(data[key], dict):
                                data[key].update(value)
                            else:
                                log_error(f'Ignoring non-dictionary value'
                                          f' for "{key}" in "{path}".')
                        else:
                            data[key] = value
                    else:
                        data[key] = value
        except Exception as exc:
            log_error(f'Failed to load JSON file "{path}".',
                      exception=exc)
    return data


class OutputRedirector:
    """
    Output redirector context manager.

    Captures and can optionally filter sys.stdout and sys.stderr.

    Automatically flushes streams before starting capture.
    """

    def __init__(self,
                 line_filter: Callable[[Text, bool], Optional[Text]] = None,
                 auto_flush: bool = False,
                 ):
        """
        Copy stdout lines to stream with optional filtering.

        :param line_filter: callable receives each stdout line and an error flag
                            and returns text or None to skip
        :param auto_flush: automatically flush captured output
        """
        self._line_filter = line_filter
        self._stdout_save: Optional[IO] = None
        self._stderr_save: Optional[IO] = None
        self._stdout_stream: Optional[IO] = None
        self._stderr_stream: Optional[IO] = None
        self._stdout_text: Optional[Text] = None
        self._stderr_text: Optional[Text] = None
        self._auto_flush = auto_flush

    @property
    def stdout_text(self) -> Text:
        """
        Property that provides captured stdout text.

        :return: captured stdout text
        """
        self.end_capture()
        return self._stdout_text

    @property
    def stderr_text(self) -> Text:
        """
        Property that provides captured stderr text.

        :return: captured stderr text
        """
        self.end_capture()
        return self._stderr_text

    def flush_stdout(self):
        """
        Flush captured and filtered stdout text to sys.stdout.
        """
        if self.stdout_text:
            sys.stdout.write(self.stdout_text)
            sys.stdout.write(os.linesep)

    def flush_stderr(self):
        """
        Flush captured and filtered stderr text to sys.stderr.
        """
        if self.stderr_text:
            sys.stderr.write(self.stderr_text)
            sys.stderr.write(os.linesep)

    def begin_capture(self):
        """
        Begin capturing stdout/stderr.

        Flush both sys streams and replace them with string streams to capture
        the output.

        Use this class as a context manager in a `with` clause, rather than
        calling this directly.
        """
        if self._stdout_save is None:
            self._stdout_save = sys.stdout
            self._stderr_save = sys.stderr
            sys.stdout.flush()
            sys.stderr.flush()
            self._stdout_stream = StringIO()
            self._stderr_stream = StringIO()
            sys.stdout = self._stdout_stream
            sys.stderr = self._stderr_stream

    def end_capture(self):
        """
        Stop capturing stdout/stderr.

        Use this class as a context manager in a `with` clause, rather than
        calling this directly.

        It is also called automatically when by `stdout_text` and `stderr_text`.
        """
        if self._stdout_text is None:
            sys.stdout = self._stdout_save
            sys.stderr = self._stderr_save
            self._stdout_stream.seek(0)
            self._stderr_stream.seek(0)
            stdout_text = self._stdout_stream.read().rstrip()
            stderr_text = self._stderr_stream.read().rstrip()
            if self._line_filter is not None:
                if stdout_text:
                    stdout_text = os.linesep.join(filter(
                        lambda line: line is not None,
                        (self._line_filter(line, True)
                         for line in stdout_text.split(os.linesep))
                    ))
                if stderr_text:
                    stderr_text = os.linesep.join(filter(
                        lambda line: line is not None,
                        (self._line_filter(line, True)
                         for line in stderr_text.split(os.linesep))
                    ))
            self._stdout_text = stdout_text
            self._stderr_text = stderr_text
            # Get ready for another round of capturing, if required.
            self._stdout_save = None
            self._stderr_save = None
            self._stdout_stream = None
            self._stderr_stream = None
            if self._auto_flush:
                self.flush_stdout()
                self.flush_stderr()

    def __enter__(self):
        self.begin_capture()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_capture()
