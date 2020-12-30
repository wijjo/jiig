"""
Jiig time adapter functions.
"""

from time import mktime

from jiig.utility.date_time import parse_date_time, parse_time_interval


def timestamp(value: str) -> float:
    """
    Adapter for string to timestamp float conversion.

    :param value: date/time string
    :return: timestamp float, as returned by mktime()
    """
    parsed_time_struct = parse_date_time(value)
    if not parsed_time_struct:
        raise ValueError('bad date/time string')
    return mktime(parsed_time_struct)


def interval(value: str) -> int:
    """
    Adapter for string to time interval conversion.

    :param value: raw text value
    :return: returned interval integer
    """
    return parse_time_interval(value)
