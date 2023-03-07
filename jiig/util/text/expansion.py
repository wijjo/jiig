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

"""
Text symbol expansion.
"""

import os
import sys
from pprint import pformat
from typing import Any

from jiig.util.options import OPTIONS


class StringExpansionError(RuntimeError):
    """String expansion exception."""

    def __init__(self, value: str, *missing_symbols: str):
        """
        Constructor.

        :param value: value that failed expansion
        :param missing_symbols: missing symbols
        """
        self.missing_symbols = missing_symbols
        unresolved = self.wrapped_symbol_string
        super().__init__(f'String expansion error: {value=} {unresolved=}')

    @property
    def wrapped_symbol_string(self) -> str:
        """
        Provide {}-wrapped symbol string for error display.

        :return: wrapped symbol string
        """
        return ' '.join([f'{{{symbol}}}' for symbol in self.missing_symbols])


def expand_value(value: Any, symbols: dict) -> str:
    """
    Produce an expanded string for a value and symbols.

    :param value: value to expand
    :param symbols: substitution symbols
    :return: expanded string
    :raise StringExpansionError: if symbols are missing, etc.
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
            raise StringExpansionError(f'Bad string expansion attribute: {attr_exc}')
        except KeyError as key_exc:
            # Strip out surrounding single quotes from exception text to get key name.
            name = str(key_exc)[1:-1]
            if not bad_names:
                symbols = symbols.copy()
            symbols[name] = '???'
            bad_names.append(name)
    return output_string
