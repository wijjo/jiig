"""
Jiig time adapter functions.
"""

from time import mktime

from jiig.utility.date_time import parse_date_time, parse_time_interval, \
    apply_date_time_delta_string


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


def age(value: str) -> float:
    """
    Adapter for age, i.e. negative time delta.

    See jiig.utility.date_time.parse_date_time_delta() for more information
    about delta strings.

    :param value: time delta string
    :return: timestamp float
    """
    return mktime(apply_date_time_delta_string(value, negative=True))
