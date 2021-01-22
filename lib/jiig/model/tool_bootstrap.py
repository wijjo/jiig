"""
Jiig tool bootstrap class.
"""

from typing import Type

from .tool import Tool
from .tool_configuration import ToolConfiguration


class ToolBootstrap(ToolConfiguration):
    """Tool bootstrap configuration and boot hook."""

    def on_boot(self) -> Type[Tool]:
        """
        Required call-back method to get Tool class.

        :return: tool class type
        """
        raise NotImplementedError
