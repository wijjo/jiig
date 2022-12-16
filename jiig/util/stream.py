# Copyright (C) 2020-2022, Steven Cooper
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

"""
Stream utilities.

For now these are read-only utilities.
"""

import json
import os
import sys
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import TracebackType
from typing import IO, Iterator, Any, AnyStr, Callable, Iterable, Type

from .log import abort
from .filesystem import create_folder
from .options import OPTIONS

# Used in open_output_file() paths to indicate a temporary file, and also to
# separate prefix from suffix.
TEMPORARY_FILE_MARKER = '?'
TEMPORARY_ROOT = '/tmp'


@contextmanager
def open_text_stream(path_or_stream: str | Path | IO,
                     unchecked: bool = False
                     ) -> Iterator[IO]:
    """
    Open a text file or stream for reading.

    A stream is just returned as is.

    :param path_or_stream: text file path or stream
    :param unchecked: pass along exceptions if True, otherwise abort
    :return: a yielded stream to use in a `with` block for proper closing
    """
    if isinstance(path_or_stream, IO):
        yield path_or_stream
    else:
        try:
            with open(path_or_stream, encoding='utf-8') as file_stream:
                yield file_stream
        except (IOError, OSError) as exc:
            if not unchecked:
                abort(f'Failed to open text file: {path_or_stream}', exc)
            raise


def read_text_file(path_or_stream: str | Path | IO,
                   unchecked: bool = False
                   ) -> str:
    """
    Read text from a text stream, given a string, file path, stream, URL, or Request object.

    :param path_or_stream: text file path or stream
    :param unchecked: pass along exceptions if True, otherwise abort
    :return: text read from source
    """
    with open_text_stream(path_or_stream, unchecked=unchecked) as file_stream:
        try:
            return file_stream.read()
        except IOError as exc:
            if not unchecked:
                abort(f'Failed to read text from {path_or_stream}.', exc)


def read_json_file(path: str | Path,
                   unchecked: bool = False
                   ) -> Any:
    """
    Read JSON from a text stream, given a string, file path, stream, URL, or Request object.

    :param path: file path
    :param unchecked: pass along exceptions if True, otherwise abort
    :return: JSON data
    """
    with open_text_stream(path, unchecked=unchecked) as file_stream:
        try:
            return json.load(file_stream)
        except (json.JSONDecodeError, IOError) as exc:
            if not unchecked:
                abort(f'Failed to read JSON data from {path}.', exc)


class OutputRedirector:
    """
    Output redirector context manager.

    Captures and can optionally filter sys.stdout and sys.stderr.

    Automatically flushes streams before starting capture.
    """

    def __init__(self,
                 line_filter: Callable[[str, bool], str | None] = None,
                 auto_flush: bool = False,
                 ):
        """
        Copy stdout lines to stream with optional filtering.

        :param line_filter: callable receives each stdout line and an error flag
                            and returns text or None to skip
        :param auto_flush: automatically flush captured output
        """
        self._line_filter = line_filter
        self._stdout_save: IO | None = None
        self._stderr_save: IO | None = None
        self._stdout_stream: IO | None = None
        self._stderr_stream: IO | None = None
        self._stdout_text: str | None = None
        self._stderr_text: str | None = None
        self._auto_flush = auto_flush

    @property
    def stdout_text(self) -> str:
        """
        Property that provides captured stdout text.

        :return: captured stdout text
        """
        self.end_capture()
        return self._stdout_text

    @property
    def stderr_text(self) -> str:
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


def open_input_file(path: str | Path,
                    binary: bool = False,
                    ) -> IO:
    """
    Convenient opening of text or binary files for reading.

    I/O exceptions are fully the caller's responsibility.

    :param path: file path
    :param binary: open the file in binary mode (defaults to utf-8 text)
    :return: open file object, usable in a `with` statement for automatic closing
    """
    kwargs = {'mode': 'r'}
    if not binary:
        kwargs['encoding'] = 'utf-8'
    return open(path, **kwargs)


class OutputFile(IO):
    """
    Special output file wrapper additional data, i.e. the file path.

    Generally not used directly. It is returned by stream.open_output_file().
    """

    def __init__(self, open_file: IO, path: str | Path | None):
        """
        Output file constructor.

        :param open_file: open file
        :param path: file path
        """
        self.open_file = open_file
        self.path = path if isinstance(path, Path) else Path(path)

    def close(self):
        """Close the file"""
        self.open_file.close()

    def fileno(self) -> int:
        """Provide the numeric file handle. See IO.fileno()."""
        return self.open_file.fileno()

    def flush(self):
        """Flush output. See IO.flush()."""
        self.open_file.flush()

    def isatty(self) -> bool:
        """Detect TTY output device. See IO.isatty()."""
        return self.open_file.isatty()

    def read(self, *args, **kwargs) -> AnyStr:
        """Read data from file. See IO.read()."""
        return self.open_file.read(*args, **kwargs)

    def readable(self) -> bool:
        """Check if file is readable. See IO.readable()."""
        return self.open_file.readable()

    def readline(self, *args, **kwargs) -> AnyStr:
        """Read line from file. See IO.readline()."""
        return self.open_file.readline(*args, **kwargs)

    def readlines(self, *args, **kwargs) -> list[AnyStr]:
        """Read lines from file. See IO.readlines()."""
        return self.open_file.readlines(*args, **kwargs)

    def seek(self, offset: int, *args, **kwargs) -> int:
        """Seek to position in file. See IO.seek()."""
        return self.open_file.seek(offset, *args, **kwargs)

    def seekable(self) -> bool:
        """Check if file is seekable. See IO.seekable()."""
        return self.open_file.seekable()

    def tell(self) -> int:
        """Report position in file. See IO.tell()."""
        return self.open_file.tell()

    def truncate(self, *args, **kwargs) -> int:
        """Truncate file. See IO.truncate()."""
        return self.open_file.truncate(*args, **kwargs)

    def writable(self) -> bool:
        """Check if file is writable. See IO.writable()."""
        return self.open_file.writable()

    def write(self, s: str) -> int:
        """Write data to file. See IO.write()."""
        return self.open_file.write(s)

    def writelines(self, lines: Iterable[str]):
        """Write lines to file. See IO.writelines()."""
        return self.open_file.writelines(lines)

    def __next__(self) -> AnyStr:
        """Iteration support. See IO.__next__()."""
        return self.open_file.__next__()

    def __iter__(self) -> Iterator[AnyStr]:
        """Iteration support. See IO.__iter__()."""
        return self.open_file.__iter__()

    def __enter__(self) -> 'OutputFile':
        """Context manager support. See IO.__enter__()."""
        return self

    def __exit__(self,
                 t: Type[BaseException] | None,
                 value: BaseException | None,
                 traceback: TracebackType | None,
                 ) -> bool | None:
        """Context manager support. See IO.__exit__()."""
        return self.open_file.__exit__(t, value, traceback)


def open_output_file(path_spec: str | Path,
                     binary: bool = False,
                     keep_temporary: bool = False,
                     create_parent_folder: bool = False,
                     ) -> OutputFile:
    """
    Convenient opening of text or binary files, temporary or permanent, for writing.

    I/O exceptions are fully the caller's responsibility.

    :param path_spec: file path, possibly including a '?' marker to create a temporary file
    :param binary: open the file in binary mode (defaults to utf-8 text)
    :param keep_temporary: do not delete temporary file if True
    :param create_parent_folder: create parent folder as needed if True
    :return: open file object, usable in a `with` statement for automatic closing
    """
    kwargs = {'mode': 'w'}
    if not binary:
        kwargs['encoding'] = 'utf-8'
    path_spec_string = str(path_spec)
    path_object = Path(path_spec)
    temporary_path_parts = path_spec_string.split(TEMPORARY_FILE_MARKER, maxsplit=1)
    if len(temporary_path_parts) == 2:
        prefix, suffix = temporary_path_parts
        if prefix:
            kwargs['prefix'] = prefix
        if suffix:
            kwargs['suffix'] = suffix
        dir_path = path_object.parent
        if dir_path:
            kwargs['dir'] = str(dir_path)
        kwargs['delete'] = not (keep_temporary or OPTIONS.debug)
        temp_file = NamedTemporaryFile(**kwargs)
        # Temporary file.
        return OutputFile(temp_file, temp_file.name)
    # Permanent file.
    if create_parent_folder:
        parent_folder = path_object.parent
        if not os.path.exists(parent_folder):
            create_folder(parent_folder)
    return OutputFile(open(path_object, **kwargs), path_object)
