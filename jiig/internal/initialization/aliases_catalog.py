# Copyright (C) 2023, Steven Cooper
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

"""Aliases catalog creation."""

from pathlib import Path
from typing import Any

from jiig.util.process import shell_command_string
from jiig.util.scoped_catalog import ScopedCatalog


def create_aliases_catalog(catalog_path: Path) -> ScopedCatalog:
    """Create aliases catalog class.

    Args:
        catalog_path: catalog file path

    Returns:
        catalog class
    """

    class AliasesCatalog(ScopedCatalog):
        """Scoped aliases catalog class."""

        path = catalog_path
        item_label = 'alias'
        payload_label = 'alias command'
        payload_label_plural = 'alias commands'

        def payload_formatter(self, name: str, payload: Any) -> str:
            """Override payload formatter in order to use shell quoting.

            Args:
                name: alias name (not used)
                payload: alias command

            Returns:
                shell-quoted formatted string
            """
            return shell_command_string(*payload)

    return AliasesCatalog()
