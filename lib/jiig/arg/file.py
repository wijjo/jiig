"""File path type."""

import os
from typing import Optional, Any, Text

from .string import String


class File(String):

    def __init__(self,
                 default_value: Text = None,
                 must_exist: bool = False,
                 absolute: bool = False,
                 allow_folder: bool = False):
        """
        File argument type constructor.

        :param default_value: default path
        :param must_exist: require that the file exists
        :param absolute: convert to absolute path
        """
        self.must_exist = must_exist
        self.absolute = absolute
        self.allow_folder = allow_folder
        super().__init__(default_value=default_value)

    def process_data(self, data: Optional[Any]) -> Optional[Any]:
        # Argparse should provide a string value.
        path = os.path.expanduser(super().process_data(data))
        exists = os.path.exists(path)
        if self.must_exist and not exists:
            raise ValueError(f'File "{path}" does not exist.')
        if exists and not self.allow_folder and not os.path.isfile(path):
            raise ValueError(f'Path "{path}" exists but is not a file.')
        if self.absolute:
            path = os.path.abspath(path)
        return path
