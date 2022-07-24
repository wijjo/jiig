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

"""Registered hints"""

from typing import Text, List, Set


class _HintRegistry:

    _supported_task_hints: Set[Text] = set()
    _used_task_hints: Set[Text] = set()
    _supported_field_hints: Set[Text] = set()
    _used_field_hints: Set[Text] = set()

    def add_supported_task_hints(self, *names: Text):
        """
        Register supported task hint name(s).

        :param names: task hint name(s)
        """
        for name in names:
            self._supported_task_hints.add(name)

    def add_used_task_hints(self, *names: Text):
        """
        Register used task hint name(s).

        :param names: task hint name(s)
        """
        for name in names:
            self._used_task_hints.add(name)

    def get_bad_task_hints(self) -> List[Text]:
        """
        Get task hints that are used, but unsupported.

        :return: bad task hints list
        """
        return list(sorted(self._used_task_hints.difference(self._supported_task_hints)))

    def add_supported_field_hints(self, *names: Text):
        """
        Register supported field hint name(s).

        :param names: field hint name(s)
        """
        for name in names:
            self._supported_field_hints.add(name)

    def add_used_field_hints(self, *names: Text):
        """
        Register used field hint name(s).

        :param names: field hint name(s)
        """
        for name in names:
            self._used_field_hints.add(name)

    def get_bad_field_hints(self) -> List[Text]:
        """
        Get field hints that are used, but unsupported.

        :return: bad field hints list
        """
        return list(sorted(self._used_field_hints.difference(self._supported_field_hints)))


HINT_REGISTRY = _HintRegistry()
