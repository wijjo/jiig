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
Field specification.

Fields are not themselves registered, but are incorporated into registered tasks.
"""

from dataclasses import dataclass
from typing import Any, Collection, Annotated

from .types import ArgumentAdapter
from .util.collections import make_list
from .util.repetition import Repetition, repetition_from_spec
from .util.types import RepeatSpec


@dataclass
class Field:
    """
    Field specification derived from type annotation.

    Use wrap_field(), instead of creating directly.
    """

    element_type: Any
    """scalar element type"""
    description: str
    """field description"""
    field_type: Any
    """field type (defaults to element_type if missing)"""
    adapters: list[ArgumentAdapter] | None
    """optional field adapter function chain"""
    repeat: Repetition | None
    """optional field repetition data"""
    choices: list | None
    """optional value choices"""


def wrap_field(element_type: Any,
               description: str = None,
               field_type: Any = None,
               adapters: Collection[ArgumentAdapter] = None,
               repeat: RepeatSpec = None,
               choices: Collection = None,
               ) -> Any:
    """
    Create Field and wrap in Annotated hint.

    :param element_type: scalar element type
    :param description: field description
    :param field_type: field type (defaults to element_type if missing)
    :param adapters: field adapter function chain
    :param repeat: optional repeat specification as count or minimum/maximum pair
    :param choices: optional value choices
    """
    field = Field(element_type,
                  description=description or '(no field description)',
                  field_type=field_type if field_type is not None else element_type,
                  adapters=make_list(adapters, allow_none=True),
                  repeat=repetition_from_spec(repeat) if repeat is not None else None,
                  choices=make_list(choices, allow_none=True))
    return Annotated[field.field_type, field]
