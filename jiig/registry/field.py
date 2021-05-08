"""
Field specification.
"""

from typing import Any, Text, Collection, Dict, Callable

from jiig.util.general import make_list

from .hints import add_used_hints

ArgumentAdapter = Callable[..., Any]


class Field:
    """Field specification derived from type annotation."""

    def __init__(self,
                 element_type: Any,
                 description: Text,
                 hints: Dict,
                 field_type: Any = None,
                 adapters: Collection[ArgumentAdapter] = None,
                 ):
        """
        Field specification constructor.

        :param element_type: scalar element type, without List or Optional type wrappers
        :param description: field description
        :param hints: hint dictionary used to customize drivers, e.g. CLI
        :param field_type: field type (defaults to element_type if missing)
        :param adapters: field adapter function chain
        """
        self.element_type = element_type
        self.field_type = field_type if field_type is not None else self.element_type
        self.description = description
        self.hints = hints
        self.adapters = make_list(adapters, allow_none=True)
        # Keep track of used hint names so that a sanity check can be performed later.
        add_used_hints(*hints.keys())

    def tweak(self,
              element_type: Any = None,
              field_type: Any = None,
              description: Text = None,
              adapters: Collection[ArgumentAdapter] = None,
              hints: Dict = None,
              ) -> 'Field':
        """
        Clone and tweak original specification.

        :param element_type: scalar element type, without List or Optional type wrappers
        :param field_type: field type, if different from element_type
        :param description: field description
        :param adapters: field adapter function chain
        :param hints: hint dictionary used to configure various front ends, e.g. CLI
        """
        if element_type is None:
            element_type = self.element_type
        if field_type is None:
            field_type = self.field_type
        if description is None:
            description = self.description
        if adapters is None:
            adapters = self.adapters
        if hints is None:
            hints = self.hints
        return Field(element_type=element_type,
                     description=description,
                     hints=hints,
                     field_type=field_type,
                     adapters=adapters)
