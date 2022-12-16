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

"""
Algorithms.
"""

from typing import Any, Sequence, Callable


def binary_search(sequence: Sequence,
                  value: Any,
                  key: Callable[[Any], Any] = None,
                  ) -> Any | None:
    """
    Perform binary search on ordered sequence.

    Based on standard bisect library, but cloned and adapted code for arbitrary
    item types and an optional key() function. Unlike find(), it returns
    the found item or None, instead of a position or -1.

    :param sequence: ordered item sequence to search
    :param value: value to search for
    :param key: optional key function a la sort() to return item key value
    :return: found item or None if not found
    """
    # "Borrowed" and adapted code from bisect.bisect_left().
    lo = 0
    hi = len(sequence)
    while lo < hi:
        mid = (lo + hi) // 2
        # Use __lt__ to match the logic in list.sort() and in heapq
        item = sequence[mid]
        if key is None:
            key_value = item
        else:
            key_value = key(item)
        if key_value < value:
            lo = mid + 1
        else:
            hi = mid
    if lo == len(sequence):
        return None
    return sequence[lo]
