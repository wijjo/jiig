# Copyright (C) 2020-2022, Steven Cooper
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

from typing import Any

from .log import abort


class JSONDict(dict):
    """Dictionary wrapper for reading JSON data as attributes."""

    def __getattr__(self, name: str) -> Any:
        """
        Access dictionary element as attribute.

        Aborts if attribute name is not present.

        :param name: attribute name
        :return: attribute value
        """
        if name not in self:
            abort(f'JSON data has no element: {name}', self)
        # Recursively wrap sub-elements.
        return _wrap_json_value(self.get(name))


def _wrap_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return JSONDict(value)
    if isinstance(value, list):
        return [_wrap_json_value(sub_value) for sub_value in value]
    if isinstance(value, tuple):
        return tuple(_wrap_json_value(sub_value) for sub_value in value)
    return value
