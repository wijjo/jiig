"""Stream utilities."""

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO
from typing import Text, IO, Iterator, Any, Dict
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
def open_text(*,
              text: Text = None,
              file: Text = None,
              stream: IO = None,
              url: Text = None,
              request: Request = None,
              timeout: int = None,
              check: bool = False
              ) -> Iterator[IO]:
    """
    Open a text stream, given a string, file path, stream, URL, or Request object.

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


def open_json(*,
              text: Text = None,
              file: Text = None,
              stream: IO = None,
              url: Text = None,
              request: Request = None,
              timeout: int = None,
              check: bool = False
              ) -> Any:
    """
    Open a text stream, given a string, file path, stream, URL, or Request object.

    :param text: input string
    :param file: file path
    :param stream: input stream
    :param url: input URL for downloading
    :param request: input Request object for downloading
    :param timeout: timeout in seconds when downloading URL or Request
    :param check: abort cleanly if True, instead of passing along exceptions
    :return: a yielded stream to use in a `with` block for proper closing
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
