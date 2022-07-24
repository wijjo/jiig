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

from typing import Any, Text, Collection, Callable, Annotated

from ..util.general import make_list
from ..util.repetition import RepeatSpec, Repetition

ArgumentAdapter = Callable[..., Any]


class Field:
    """Field specification derived from type annotation."""

    def __init__(self,
                 element_type: Any,
                 description: Text = None,
                 field_type: Any = None,
                 adapters: Collection[ArgumentAdapter] = None,
                 repeat: RepeatSpec = None,
                 choices: Collection = None,
                 ):
        """
        Field specification constructor.

        :param element_type: scalar element type, without List or Optional type wrappers
        :param description: field description
        :param field_type: field type (defaults to element_type if missing)
        :param adapters: field adapter function chain
        :param repeat: optional repeat specification as count or minimum/maximum pair
        :param choices: optional value choices
        """
        self.element_type = element_type
        self.field_type = field_type if field_type is not None else self.element_type
        self.description = description or '(no field description)'
        self.repeat = Repetition.from_spec(repeat)
        self.choices = make_list(choices)
        self.adapters = make_list(adapters, allow_none=True)

    @classmethod
    def wrap(cls,
             element_type: Any,
             description: Text = None,
             field_type: Any = None,
             adapters: Collection[ArgumentAdapter] = None,
             repeat: RepeatSpec = None,
             choices: Collection = None,
             ) -> Any:
        """
        Create Field and wrap in Annotated hint.

        :param element_type: scalar element type, without List or Optional type wrappers
        :param description: field description
        :param field_type: field type (defaults to element_type if missing)
        :param adapters: field adapter function chain
        :param repeat: optional repeat specification as count or minimum/maximum pair
        :param choices: optional value choices
        """
        field = Field(element_type,
                      description=description,
                      field_type=field_type,
                      adapters=adapters,
                      repeat=repeat,
                      choices=choices)
        return Annotated[field.field_type, field]
