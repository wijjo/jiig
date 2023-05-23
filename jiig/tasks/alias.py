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

"""Create and manage task command aliases.

IMPORTANT: The task function name must be "alias" to allow startup code to
implement special alias command detection and argument list pre-processing to
insert "--" before parsing command line arguments.
"""

import jiig

from ._common import handle_action


# noinspection PyShadowingBuiltins
@jiig.task
def alias(
    runtime: jiig.Runtime,
    name: jiig.f.text() = None,
    command: jiig.f.text() = None,
    arguments: jiig.f.text(repeat=()) = None,
    comment: jiig.f.text() = None,
    delete: jiig.f.boolean() = None,
    all: jiig.f.boolean() = None,
):
    """Multi-mode alias management.

    # Mode 1: Set alias

    Given a command: Create or update alias. Scope required if any exist. Add
    comment if provided.

    # Mode 2: Delete alias

    When delete is True: Delete alias. Scope required if any exist.

    # Mode 3: Display alias(es)

    Display aliases, filtered by name[@scope], if provided.

    Args:
        runtime: jiig Runtime API
        name: alias name with optional "@scope" specifier
        command: aliased command name
        arguments: aliased command arguments
        comment: alias comment
        delete: delete matching alias if enabled
        all: show all scopes if enabled, otherwise show only active scopes
    """
    if command is not None:
        if not arguments:
            runtime.abort('Command arguments are required when setting an alias.')
        payload = [command] + arguments
        check_arguments_result = runtime.internal.driver.check_arguments(payload)
        if check_arguments_result.error is not None:
            runtime.abort('Bad alias command.', check_arguments_result.error)
    else:
        payload = None
    handle_action(
        runtime.internal.aliases_catalog,
        name=name,
        payload=payload,
        delete=delete,
        comment=comment,
        show=payload is None and comment is None and not delete,
        all=all,
    )
