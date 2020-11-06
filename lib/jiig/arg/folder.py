"""Folder path type."""

import os

from jiig.external.argument import arg_type_factory, arg_type
from jiig.typing import ArgumentTypeConversionFunction


@arg_type_factory
def folder_path(must_exist: bool = False,
                absolute: bool = False
                ) -> ArgumentTypeConversionFunction:
    """
    Folder parameterized argument type function.

    :param must_exist: require that the folder exists
    :param absolute: convert to absolute path
    :return: parameterized closure function to perform checking and conversion
    """
    @arg_type
    def folder_path_inner(value: str) -> str:
        path = os.path.expanduser(value)
        exists = os.path.exists(path)
        if must_exist and not exists:
            raise ValueError(f'Folder "{path}" does not exist.')
        if exists and not os.path.isdir(path):
            raise ValueError(f'Path "{path}" exists but is not a folder.')
        if absolute:
            path = os.path.abspath(path)
        return path
    return folder_path_inner
