"""File path type."""

import os

from jiig.external.argument import arg_type_factory, arg_type
from jiig.typing import ArgumentTypeConversionFunction


@arg_type_factory
def file_path(must_exist: bool = False,
              absolute: bool = False,
              allow_folder: bool = False
              ) -> ArgumentTypeConversionFunction:
    """
    File parameterized argument type function.

    :param must_exist: require that the file exists
    :param absolute: convert to absolute path
    :param allow_folder: allow a folder path if True
    :return: parameterized closure function to perform checking and conversion
    """
    @arg_type
    def file_path_inner(value: str) -> str:
        path = os.path.expanduser(value)
        exists = os.path.exists(path)
        if must_exist and not exists:
            raise ValueError(f'File "{path}" does not exist.')
        if exists and not allow_folder and not os.path.isfile(path):
            raise ValueError(f'Path "{path}" exists but is not a file.')
        if absolute:
            path = os.path.abspath(path)
        return path
    return file_path_inner
