"""
Functional support for argument types. (WIP)
"""

import os
from functools import wraps
from time import mktime
from typing import Callable, Dict

from jiig.utility.date_time import parse_date_time, parse_time_interval


REGISTERED_ARG_TYPES: Dict[int, Callable] = {}


def arg_type(function: Callable = None):
    def decorator(decorated_function):
        @wraps(decorated_function)
        def wrapper(value):
            return decorated_function(value)
        REGISTERED_ARG_TYPES[id(decorated_function)] = decorated_function
        return wrapper
    if function is None:
        return decorator
    return decorator(function)


@arg_type
def integer(value: str) -> int:
    return int(value)


@arg_type
def boolean(value: bool) -> bool:
    return value


@arg_type
def text(value: str) -> str:
    return value


@arg_type
def date_time(value: str) -> float:
    parsed_time_struct = parse_date_time(value)
    if not parsed_time_struct:
        raise ValueError(f'Bad date/time string "{value}".')
    return mktime(parsed_time_struct)


def file_path(must_exist: bool = False,
              absolute: bool = False,
              allow_folder: bool = False
              ) -> Callable[[str], str]:
    @arg_type
    def wrapper(value: str) -> str:
        path = os.path.expanduser(value)
        exists = os.path.exists(path)
        if must_exist and not exists:
            raise ValueError(f'File "{path}" does not exist.')
        if exists and not allow_folder and not os.path.isfile(path):
            raise ValueError(f'Path "{path}" exists but is not a file.')
        if absolute:
            path = os.path.abspath(path)
        return path
    return wrapper


def folder_path(must_exist: bool = False,
                absolute: bool = False
                ) -> Callable[[str], str]:
    @arg_type
    def wrapper(value: str) -> str:
        path = os.path.expanduser(value)
        exists = os.path.exists(path)
        if must_exist and not exists:
            raise ValueError(f'Folder "{path}" does not exist.')
        if exists and not os.path.isdir(path):
            raise ValueError(f'Path "{path}" exists but is not a folder.')
        if absolute:
            path = os.path.abspath(path)
        return path
    return wrapper


@arg_type
def interval(value: str) -> int:
    return parse_time_interval(value)
