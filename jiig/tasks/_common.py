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

"""Common functions supporting Jiig tasks."""

from typing import Any

from jiig.util.log import log_error
from jiig.util.scoped_catalog import (
    ScopedCatalog,
    ScopedCatalogResult,
)


# noinspection PyShadowingBuiltins
def handle_action(catalog: ScopedCatalog,
                  *,
                  name: str = None,
                  payload: Any = None,
                  comment: str = None,
                  delete: bool = False,
                  show: bool = False,
                  all: bool = False,
                  ) -> bool:
    """Handle all possible actions based on provided options and data.

    Makes it easier to implement multi-mode commands and functions.

    Action combinations that make no sense are rejected by aborting.

    Args:
        catalog: scoped catalog to invoke for actions
        name: optional name needed for set and delete actions
        payload: optional payload to set
        comment: optional comment to set
        delete: delete named item or payload if True
        show: show items/payloads if True
        all: show all scopes if enabled, otherwise show only active scopes

    Returns:
        True if action was successful
    """
    # Validation gauntlet to reject bad action combinations.
    if name is None and (delete or payload is not None or comment is not None):
        log_error(f'Catalog action requires a name.')
        return False
    if delete and (payload is not None or comment is not None):
        log_error(f'Catalog delete action may not be combined with set action.')
        return False
    if comment is not None and (delete or show):
        log_error(f'Catalog set comment action may not be combined with delete'
                  f' or show action.')
        return False
    if all and (payload is not None or comment is not None or delete):
        log_error(f'All option only applies to catalog show action.')
        return False
    # Handle needed action(s).
    result: ScopedCatalogResult | None = None
    if payload is not None:
        result = catalog.set(name, payload, verbose=True)
    if comment is not None:
        result = catalog.comment(name, comment, verbose=True)
    if delete:
        result = catalog.delete(name, verbose=True, confirm=True)
    if show:
        catalog.show(name=name, active=None if all else True)
    if result is not None:
        if result.errors:
            return False
        catalog.save()
    return True
