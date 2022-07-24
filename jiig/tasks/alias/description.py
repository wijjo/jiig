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
Alias description task.
"""

import jiig


@jiig.task
def description_(
    runtime: jiig.Runtime,
    alias: jiig.f.text(),
    description: jiig.f.text(),
):
    """
    Set alias description.

    :param runtime: Jiig runtime API.
    :param alias: Target alias name for description.
    :param description: Alias description.
    """
    with runtime.open_alias_catalog() as catalog:
        description_text = ' '.join(description)
        catalog.update_alias(alias, description=description_text)
