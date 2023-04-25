# Copyright (C) 2021-2023, Steven Cooper
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

"""Alias set task."""

import jiig


@jiig.task
def set_(
    runtime: jiig.Runtime,
    description: jiig.f.text(),
    alias: jiig.f.text(),
    command: jiig.f.text(),
    command_arguments: jiig.f.text(repeat=(1, None)),
):
    """Create or update alias.

    Args:
        runtime: jiig Runtime API.
        description: New alias description.
        alias: Name of alias to create or update.
        command: Aliased command name.
        command_arguments: Aliased command arguments.
    """
    with runtime.open_alias_catalog() as catalog:
        if catalog.get_alias(alias):
            catalog.update_alias(alias,
                                 command=[command] + command_arguments,
                                 description=description)
        else:
            catalog.create_alias(alias,
                                 [command] + command_arguments,
                                 description=description)
