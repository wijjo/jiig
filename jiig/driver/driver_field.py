"""Driver field data."""

from typing import Text, Any, Dict, Sequence

from ..util.general import DefaultValue
from ..util.repetition import Repetition


class DriverField:
    """Field data fed to driver."""
    def __init__(self,
                 name: Text,
                 description: Text,
                 element_type: Any,
                 hints: Dict,
                 repeat: Repetition = None,
                 default: DefaultValue = None,
                 choices: Sequence = None,
                 ):
        """
        Driver field constructor.

        :param name: field name
        :param description: field description
        :param element_type: field element type
        :param hints: raw hint dictionary
        :param repeat: optional repeat data
        :param default:
        :param choices:
        """
        self.name = name
        self.description = description
        self.element_type = element_type
        self.hints = hints
        self.repeat = repeat
        self.default = default
        self.choices = choices
