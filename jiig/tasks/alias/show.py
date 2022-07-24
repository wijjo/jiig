# Copyright (C) 2021-2022, Steven Cooper
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

"""
Show alias(es) task.
"""

import jiig


@jiig.task
def show(
    runtime: jiig.Runtime,
    aliases: jiig.f.text(repeat=(1, None)),
):
    """
    Display alias(es).

    :param runtime: jiig Runtime API.
    :param aliases: Alias name(s) to display.
    """
    with runtime.open_alias_catalog() as catalog:
        for name in aliases:
            resolved_alias = catalog.get_alias(name)
            if resolved_alias is not None:
                runtime.message(resolved_alias)
            else:
                runtime.error(f'Alias "{name}" does not exist.')
