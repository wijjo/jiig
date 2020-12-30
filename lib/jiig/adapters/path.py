"""
Jiig path adapter functions.
"""

import os


def check_exists(value: str) -> str:
    """
    Adapter that checks if a path exists.

    :param value: file or folder path
    :return: unchanged path
    """
    if not os.path.exists(value):
        raise ValueError('path does not exist')
    return value


def check_folder(value: str) -> str:
    """
    Adapter that checks if a path is a folder.

    :param value: path string
    :return: unchanged path
    """
    if not os.path.isdir(value):
        raise ValueError('path is not a folder')
    return value


def check_file(value: str) -> str:
    """
    Adapter that checks if a path is a file.

    :param value: path string
    :return: unchanged path
    """
    if not os.path.isfile(value):
        raise ValueError('path is not a file')
    return value


def expand_user(value: str) -> str:
    """
    Adapter that expands a user path, e.g. that starts with "~/".

    :param value: path string
    :return: expanded path string
    """
    return os.path.expanduser(value)


def expand_environment(value: str) -> str:
    """
    Adapter that expands a path with environment variables.

    :param value: path string
    :return: expanded path string
    """
    return os.path.expandvars(value)


def absolute(value: str) -> str:
    """
    Adapter that makes a path absolute.

    :param value: path string
    :return: absolute path string
    """
    return os.path.abspath(value)
