# Copyright (C) 2020-2023, Steven Cooper
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

"""Text symbol expansion."""

import os
import sys
from pprint import pformat
from typing import Any

from jiig.util.options import OPTIONS


class StringExpansionError(RuntimeError):
    """String expansion exception."""

    def __init__(self, value: str, *missing: str):
        """Constructor.

        Args:
            value: value that failed expansion
            *missing: missing symbols
        """
        self.value = value
        self.missing = list(missing)
        self.missing_string = ' '.join([f'{symbol}' for symbol in missing])
        super().__init__()

    def __str__(self) -> str:
        """Provide string for exception.

        Returns:
            exception string
        """
        return super().__str__() + f'value="{self.value}" missing={self.missing}'


def expand_value(value: Any, symbols: dict) -> str:
    """Produce an expanded string for a value and symbols.

    Args:
        value: value to expand
        symbols: substitution symbols

    Returns:
        expanded string

    Raises:
        StringExpansionError: if symbols are missing, etc.
    """
    if isinstance(value, (tuple, list)):
        return ' '.join([expand_value(element, symbols) for element in value])
    if not isinstance(value, str):
        return str(value)
    output_string: str | None = None
    bad_names: list[str] = []
    # The loop allows all unresolved symbols to be discovered.
    while output_string is None:
        try:
            output_string = value.format(**symbols)
            if bad_names:
                if OPTIONS.debug:
                    sys.stderr.write(f'--- symbols ---{os.linesep}')
                    sys.stderr.write(f'{pformat(symbols, indent=2)}{os.linesep}')
                    sys.stderr.write(f'---{os.linesep}')
                raise StringExpansionError(value, *bad_names)
        except AttributeError as attr_exc:
            sys.stderr.write(f'--- expansion string ---{os.linesep}')
            sys.stderr.write(f'{pformat(value, indent=2)}{os.linesep}')
            sys.stderr.write(f'---{os.linesep}')
            raise StringExpansionError(f'String expansion attribute: {attr_exc}')
        except KeyError as key_exc:
            # Strip out surrounding single quotes from exception text to get key name.
            name = str(key_exc)[1:-1]
            if not bad_names:
                symbols = symbols.copy()
            symbols[name] = '???'
            bad_names.append(name)
    return output_string
