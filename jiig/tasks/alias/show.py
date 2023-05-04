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

"""Show alias(es) task."""

import jiig
from jiig.util.process import shell_command_string

@jiig.task
def show(
    runtime: jiig.Runtime,
    aliases: jiig.f.text(repeat=(1, None)),
):
    """Display alias(es).

    Args:
        runtime: jiig Runtime API.
        aliases: Alias name(s) to display.
    """
    with runtime.open_alias_catalog() as catalog:
        for name in aliases:
            resolved_alias = catalog.get_alias(name)
            if resolved_alias is not None:
                message = f'''
Alias: {resolved_alias.name}
{resolved_alias.description}
{shell_command_string(*resolved_alias.command)}
'''.strip()
                runtime.message(message)
            else:
                runtime.error(f'Alias "{name}" does not exist.')
