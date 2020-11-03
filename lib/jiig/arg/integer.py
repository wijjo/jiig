"""Integer argument type."""

from typing import Text, Optional, Any

from .argument_type import ArgumentType


class Integer(ArgumentType):

    def __init__(self,
                 minimum: Optional[int] = None,
                 maximum: Optional[int] = None,
                 default_value: Text = None):
        """
        Integer constructor.

        :param minimum: minimum value
        :param maximum: maximum value
        :param default_value: default integer value
        """
        self.minimum = minimum
        self.maximum = maximum
        super().__init__(default_value=default_value)

    def process_data(self, data: Optional[Any]) -> Optional[Any]:
        # Argparse should provide a string value.
        value = int(data)
        if self.minimum is not None and value < self.minimum:
            raise ValueError(f'Integer value {value} is less than the'
                             f' minimum, {self.minimum}.')
        if self.maximum is not None and value > self.maximum:
            raise ValueError(f'Integer value {value} is greater than the'
                             f' maximum, {self.maximum}.')
        return value
