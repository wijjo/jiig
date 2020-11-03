"""Date/time argument type, produces timestamp values."""

from time import mktime
from typing import Text, Optional, Any

from jiig.utility.date_time import parse_date_time
from .argument_type import ArgumentType


class DateTime(ArgumentType):

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
        parsed_time_struct = parse_date_time(data)
        if not parsed_time_struct:
            raise ValueError(f'Bad date/time string "{data}".')
        return mktime(parsed_time_struct)
