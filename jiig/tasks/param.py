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

"""Create and manage tool parameters."""

import jiig

from ._common import handle_action


# noinspection PyShadowingBuiltins
@jiig.task
def param(
    runtime: jiig.Runtime,
    name: jiig.f.text() = None,
    value: jiig.f.text(repeat=()) = None,
    delete: jiig.f.boolean() = None,
    all: jiig.f.boolean() = None,
):
    """Tool parameter management.

    Parameters may be a list, but only if they have a list default value.

    # Mode 1: Set parameter

    Given a vale: Create or update parameter. Scope required if any exist. Add
    comment if provided.

    # Mode 2: Delete parameter value

    When delete is True: Delete parameter. Scope required if any exist.

    # Mode 3: Display parameter(s)

    Display parameters, filtered by name[@scope], if provided.

    Args:
        runtime: jiig Runtime API
        name: parameter name with optional "@scope" specifier
        value: parameter value
        delete: delete matching parameter value if enabled
        all: show all scopes if enabled, otherwise show only active scopes
    """
    if value:
        unscoped_name, _scope = runtime.internal.params_catalog.split_name(name)
        default_value = runtime.internal.params_catalog.defaults.get(unscoped_name)
        if not isinstance(default_value, list):
            if len(value) > 1:
                runtime.abort(f'Parameter only accepts a simple value: {unscoped_name}')
            value = value[0]
    else:
        value = None
    # Check if default is a list before accepting a list.
    handle_action(
        runtime.internal.params_catalog,
        name=name,
        payload=value,
        delete=delete,
        comment=None,
        show=value is None and not delete,
        all=all,
    )
