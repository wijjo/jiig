"""Date/time argument type, produces timestamp values."""

from time import mktime

from jiig.external.argument import arg_type
from jiig.utility.date_time import parse_date_time


@arg_type
def date_time(value: str) -> float:
    parsed_time_struct = parse_date_time(value)
    if not parsed_time_struct:
        raise ValueError(f'Bad date/time string "{value}".')
    return mktime(parsed_time_struct)
