# Copyright (C) 2023, Steven Cooper
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

"""Input prompting utilities."""

from typing import Iterable

from .log import log_error


def text_prompt(label: str,
                default: str = None,
                choices: Iterable[str] = None,
                ) -> str:
    """
    Prompt for user input.

    Retry if choices are specified and the input does not match any given choice.

    Args:
        label: prompt label
        default: optional default text if no input is given
        choices: optional choices to restrict input

    Returns:
        input text
    """
    if choices:
        if default is not None and default not in choices:
            log_error(f'Prompt default "{default}" is not a valid choice.')
            default = None
        choices_trailer = f' [{"|".join(choices)}]'
    else:
        choices_trailer = ''
    if default:
        default_trailer = f' ("{default}")'
    else:
        default_trailer = ''
    while True:
        value = input(f'{label}{choices_trailer}{default_trailer}: ')
        value = value.strip()
        if not value:
            value = default
        if value and (not choices or value in choices):
            return value
        if value:
            log_error('Input must be one of:', *choices)
        else:
            log_error('Input is required.')


def boolean_prompt(label: str,
                   default: bool = None,
                   ) -> bool:
    """
    Yes/no prompt.

    Args:
        label: prompt label
        default: optional default boolean

    Returns:
        True if answered in the positive (y|yes)
    """
    if default is not None:
        default_text = 'yes' if default else 'no'
    else:
        default_text = None
    response = text_prompt(label, default=default_text, choices=('y', 'yes', 'n', 'no'))
    return response in ('y', 'yes')
