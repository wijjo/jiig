"""Date/time argument type, produces timestamp values."""

from jiig.utility.date_time import parse_time_interval
from jiig.external.argument import arg_type


@arg_type(str)
def interval(value: str) -> int:
    """
    Interval argument type function.

    :param value: raw text value
    :return: returned interval integer
    """
    return parse_time_interval(value)
