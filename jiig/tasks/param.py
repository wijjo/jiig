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

import json

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

    The name can have an optional "@scope" specifier, where scope is a relative
    or absolute filesystem path. Scoped values apply at and below the path.

    Values apply either to a specific scope, or they default to the active or
    global scope, if "@scope" was not provided.

    Parameter values will be saved as a list when the default value is a list.
    List values may either be specified as separate arguments or as a single
    JSON-style list argument string.

    List strings will be parsed using json.loads(). This allow for direct copy,
    paste, and tweaking from a parameter listing. See example below with a list
    string argument.

        <tool-name> param mylistparam '["aaa", "bbb", "ccc"]'

    If a value is not provided then parameters and values are listed, filtering
    on an optional name[@scope] specification.

    Args:
        runtime: jiig Runtime API
        name: parameter name with optional "@scope" specifier
        value: parameter value
        delete: delete matching parameter value if enabled
        all: show all scopes if enabled, otherwise show only active scopes
    """
    if value:
        unscoped_name, _scope = runtime.internal.params_catalog.split_name(name)
        if runtime.internal.params_catalog.item_has_list_payloads(unscoped_name):
            # Try JSON parsing to convert a single value that looks like a list.
            if (len(value) == 1
                    and isinstance(value[0], str)
                    and len(value[0]) >= 2
                    and value[0][0] == '[' and value[0][-1] == ']'):
                try:
                    value = json.loads(value[0])
                except json.JSONDecodeError as exc:
                    runtime.error(f'Failed to parse parameter value list string: {exc}')
        else:
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
