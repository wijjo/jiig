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
Alias list task.
"""

from typing import Text, Iterable, Iterator

import jiig
from jiig.util.alias_catalog import Alias
from jiig.util.text import format_table


@jiig.task(
    cli={
        'options': {
            'expand_names': ('-e', '--expand-names'),
        }
    }
)
def list_(
    runtime: jiig.Runtime,
    expand_names: jiig.f.boolean(),
):
    """
    List aliases.

    :param runtime: Jiig runtime API.
    :param expand_names: Display expanded paths in names.
    """
    displayed_line_count = 0
    with runtime.open_alias_catalog() as catalog:
        for line in _format_aliases(catalog.iterate_aliases(), long_names=expand_names):
            runtime.message(line)
            displayed_line_count += 1
    # _format_aliases() returns no lines, not even a heading, if no aliases exist.
    if displayed_line_count == 0:
        runtime.message('No aliases exist.')


def _format_aliases(aliases: Iterable[Alias],
                    long_names=False,
                    ) -> Iterator[Text]:
    # Keep alias labels grouped and sorted by path within the group.
    raw_rows = sorted([
        (iter_alias.name if long_names else iter_alias.short_name,
         iter_alias.description,
         iter_alias.command_string,
         iter_alias.label,
         (iter_alias.path if long_names else iter_alias.short_path) or '')
        for iter_alias in aliases
    ], key=lambda row: (row[3], row[4]))
    if raw_rows:
        rows = [row[:3] for row in raw_rows]
        for line in format_table(*rows, headers=['alias', 'description', 'command']):
            yield line
