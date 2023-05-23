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

"""Parameters catalog creation."""

from pathlib import Path
from typing import Any

from jiig.util.scoped_catalog import ScopedCatalog


def create_params_catalog(catalog_path: Path,
                          defaults: dict[str, Any] = None,
                          comments: dict[str, str] = None,
                          ) -> ScopedCatalog:
    """Create parameters catalog class.

    Args:
        catalog_path: catalog file path
        defaults: optional tool parameter defaults
        comments: optional tool parameter comments

    Returns:
        catalog class
    """
    class ParamsCatalog(ScopedCatalog):
        """Scoped parameters catalog class."""
        path = catalog_path
        item_label = 'parameter'
        payload_label = 'parameter value'
        payload_label_plural = 'parameter values'
        locked = True
    catalog = ParamsCatalog(defaults=defaults, comments=comments)
    catalog.save()
    return catalog
