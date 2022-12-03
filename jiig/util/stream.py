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
from contextlib import contextmanager, AbstractContextManager
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import TracebackType
from typing import Text, IO, Iterator, Any, Dict, Optional, Callable, AnyStr, Iterable, Type, List
from urllib.request import urlopen, Request

from .log import abort, log_error
from .filesystem import get_folder_stack, create_folder
from .options import OPTIONS

# Used in open_output_file() paths to indicate a temporary file, and also to
# separate prefix from suffix.
TEMPORARY_FILE_MARKER = '?'

TEMPORARY_ROOT = '/tmp'


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


def open_input_file(path: str, binary: bool = False) -> IO:
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

    def __init__(self, open_file: IO, path: Optional[str]):
        """
        Output file constructor.

        :param open_file: open file
        :param path: file path
        """
        self.open_file = open_file
        self.path = path

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

    def readlines(self, *args, **kwargs) -> List[AnyStr]:
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
                 t: Optional[Type[BaseException]],
                 value: Optional[BaseException],
                 traceback: Optional[TracebackType],
                 ) -> Optional[bool]:
        """Context manager support. See IO.__exit__()."""
        return self.open_file.__exit__(t, value, traceback)


def open_output_file(path: str,
                     binary: bool = False,
                     keep_temporary: bool = False,
                     create_parent_folder: bool = False,
                     ) -> OutputFile:
    """
    Convenient opening of text or binary files, temporary or permanent, for writing.

    I/O exceptions are fully the caller's responsibility.

    :param path: file path, possibly including a '?' marker to create a temporary file
    :param binary: open the file in binary mode (defaults to utf-8 text)
    :param keep_temporary: do not delete temporary file if True
    :param create_parent_folder: create parent folder as needed if True
    :return: open file object, usable in a `with` statement for automatic closing
    """
    kwargs = {'mode': 'w'}
    if not binary:
        kwargs['encoding'] = 'utf-8'
    temporary_path_parts = path.split(TEMPORARY_FILE_MARKER, maxsplit=1)
    if len(temporary_path_parts) == 2:
        prefix, suffix = temporary_path_parts
        if prefix:
            kwargs['prefix'] = prefix
        if suffix:
            kwargs['suffix'] = suffix
        dir_path = os.path.dirname(path)
        if dir_path:
            kwargs['dir'] = dir_path
        kwargs['delete'] = not (keep_temporary or OPTIONS.debug)
        temp_file = NamedTemporaryFile(**kwargs)
        # Temporary file.
        return OutputFile(temp_file, temp_file.name)
    # Permanent file.
    if create_parent_folder:
        parent_folder = os.path.dirname(path)
        if not os.path.exists(parent_folder):
            create_folder(parent_folder)
    return OutputFile(open(path, **kwargs), path)


@dataclass
class FileMakerOutputFile:
    """Data returned by FileMaker.open()."""
    stream: IO
    path: Path

    def write(self, s: AnyStr, end_line: bool = False, flush: bool = True):
        """
        Convenience wrapper for stream.write().

        :param s: string/bytes to write to output stream
        :param end_line: add line separator if True
        :param flush: flush output stream if True
        """
        self.stream.write(s)
        if end_line:
            self.stream.write(os.linesep)
        if flush:
            self.stream.flush()

    def write_lines(self, *lines: AnyStr, flush: bool = False):
        """
        Write zero or more lines to output stream with line endings.

        :param lines: lines (strings or bytes) to write to output stream
        :param flush: flush output stream if True
        """
        for line in lines:
            self.write(line, end_line=True)
        if flush:
            self.stream.flush()


class FileMaker:
    """Creates and opens temporary or permanent files."""

    def __init__(self,
                 base_folder: str | Path = None,
                 sub_folder: str | Path = None,
                 prefix: str = None,
                 suffix: str = None,
                 encoding: str = None,
                 temporary: bool = False,
                 overwrite: bool = False,
                 ):
        """
        Constructor.

        :param base_folder: optional override base folder (default: /tmp)
        :param sub_folder: optional sub-folder (default: no sub-folder)
        :param prefix: optional file prefix string
        :param suffix: optional file suffix string
        :param encoding: optional text encoding
        :param temporary: use temporary name and automatically delete if True
        :param overwrite: overwrite existing file if True, otherwise generate new name
        """
        if base_folder:
            self.folder = Path(base_folder).expanduser()
        else:
            self.folder = Path(TEMPORARY_ROOT)
        if sub_folder:
            self.folder = self.folder / sub_folder
            if not self.folder.exists():
                os.makedirs(self.folder)
        self.prefix = prefix or ''
        self.suffix = suffix or ''
        self.encoding = encoding
        self.temporary = temporary
        self.overwrite = overwrite

    def get_path(self, name: str = None, ignore_existing: bool = False) -> Path:
        """
        Determine file path.

        Do not use for temporary files.

        :param name: file base name
        :param ignore_existing: ignore existing file if True, even if self.overwrite is False
        :return: full file path
        """
        name_parts: list[str] = []
        if self.prefix:
            name_parts.append(self.prefix)
        if name:
            name_parts.append(name)
        if not name_parts:
            name_parts.append('file')
        base_name = '_'.join(name_parts)
        path = self.folder / f'{base_name}{self.suffix}'
        if not ignore_existing and not self.overwrite:
            counter = 0
            while os.path.exists(path):
                counter += 1
                path = os.path.join(self.folder, f'{base_name}_{counter}{self.suffix}')
        return path

    @contextmanager
    def open(self, name: str = None) -> AbstractContextManager[FileMakerOutputFile]:
        """
        Create and open file as a context manager.

        Close file stream when context `with` block ends.

        :param name: file base name
        :return: (stream, path) tuple
        """
        if self.temporary:
            prefix_parts = [part for part in [self.prefix, name] if part is not None]
            full_prefix = f'{"_".join(prefix_parts)}_' if prefix_parts else None
            with NamedTemporaryFile(mode='w',
                                    encoding=self.encoding,
                                    suffix=self.suffix,
                                    prefix=full_prefix,
                                    dir=self.folder,
                                    ) as fp:
                yield FileMakerOutputFile(fp, Path(fp.name))
        else:
            path = self.get_path(name=name)
            try:
                with open(path, 'w', encoding='utf-8') as stream:
                    yield FileMakerOutputFile(stream, path)
            except (IOError, OSError) as exc:
                abort(f'Failed to open temporary file: {path}', exception=exc)
