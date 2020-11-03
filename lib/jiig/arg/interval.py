"""Date/time argument type, produces timestamp values."""

from typing import Text, Optional, Any

from jiig.utility.date_time import parse_time_interval
from .argument_type import ArgumentType


class Interval(ArgumentType):

    def __init__(self, default_value: Text = None):
        """
        DateTime constructor.

        :param default_value: default date/time string value
        """
        super().__init__(default_value=default_value)

    def process_data(self, data: Optional[Any]) -> Optional[Any]:
        # Argparse should provide a string value.
        if data is None:
            return None
        return parse_time_interval(data)
