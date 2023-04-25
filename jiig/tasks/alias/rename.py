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

"""Alias rename task."""

import jiig


@jiig.task
def rename(
    runtime: jiig.Runtime,
    alias: jiig.f.text(),
    alias_new: jiig.f.text(),
):
    """Rename alias.

    Args:
        runtime: Jiig runtime API.
        alias: Existing alias name.
        alias_new: New alias name.
    """
    with runtime.open_alias_catalog() as catalog:
        catalog.rename_alias(alias, alias_new)
