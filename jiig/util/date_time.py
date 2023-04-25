# Copyright (C) 2020-2023, Steven Cooper
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

"""Jiig date/time utilities."""

import datetime
import re
from time import (
    localtime,
    mktime,
    strftime,
    struct_time,
)
from dataclasses import dataclass

from .log import log_error, log_warning

DATE_DELTA_LETTERS = 'ymwd'
TIME_DELTA_LETTERS = 'HMS'
DATE_TIME_DELTA_LETTERS = DATE_DELTA_LETTERS + TIME_DELTA_LETTERS

TIMESTAMP_SEPARATOR_REGEX = re.compile(r'[.\-_]')
# Compiled regular expression for timestamp format strings. '.', '-', and '_'
# separator characters are allowed in front of a string, at the end of a string,
# and between date/time specifiers.
TIMESTAMP_FORMAT_REGEX = re.compile(
    rf'^%s$' % rf'({TIMESTAMP_SEPARATOR_REGEX.pattern})?'.join(
        [
            '',
            r'(yyyy|yy)?',
            r'(mm)?',
            r'(dd)?',
            r'(hh)?',
            r'(mm)?',
            r'(ss)?',
        ]
    )
)
TIMESTAMP_DEFAULT_STRFTIME_FORMAT = '%Y%m%d%H%M%S'


@dataclass
class DateTimeDelta:
    """Date/Time delta data."""
    years: int
    months: int
    weeks: int
    days: int
    hours: int
    minutes: int
    seconds: int


def parse_date_time_delta(delta_string: str | None,
                          negative: bool = False,
                          default_letter: str = None,
                          date_only: bool = False,
                          time_only: bool = False,
                          ) -> DateTimeDelta:
    """Parse a time delta and convert to a DateTimeDelta object.

    Time delta strings are comma-separated individual deltas to apply to a
    single date/time component.

    Each component delta is an integer followed by an optional letter indicting
    time period, where the letters have the following assigned meanings. Similar
    to strftime() formats, time values use uppercase letters and date values use
    lowercase.

        letter  description
        ======  ==================================
        S       seconds
        M       minutes
        H       hours
        d       days
        w       weeks
        m       months
        y       years
        (none)  based on default_letter or seconds if not specified

    Args:
        delta_string: time delta specification
        negative: apply in a reverse time direction if True
        default_letter: letter substituted when none provided for value
            (default: 's')
        date_only: only accept date (ymwd) values
        time_only: only accept time (HMS) values

    Returns:
        DateTimeDelta object
    """
    if date_only:
        if time_only:
            valid_letters = ''
            label = ''
        else:
            valid_letters = DATE_DELTA_LETTERS
            label = ' date'
    elif time_only:
        valid_letters = TIME_DELTA_LETTERS
        label = ' time'
    else:
        valid_letters = DATE_TIME_DELTA_LETTERS
        label = ' date/time'
    if default_letter:
        # noinspection SpellCheckingInspection
        if default_letter not in valid_letters:
            log_error(f'Bad{label} default_letter "{default_letter}" '
                      f'passed to parse_date_time_delta().')
            default_letter = None
    else:
        default_letter = 's'
    # Get values by period letter.
    values: dict[str, int] = {}
    if delta_string:
        for part in delta_string.split(','):
            if part:
                value = None
                letter = default_letter
                try:
                    if part[-1].isdigit():
                        value = int(part)
                    elif len(part) > 1:
                        value = int(part[:-1])
                        letter = part[-1]
                except ValueError:
                    pass
                if letter in valid_letters:
                    if value is not None:
                        if letter in values:
                            values[letter] += value
                        else:
                            values[letter] = value
                else:
                    log_warning(f'Bad{label} delta specification "{part}"'
                                f' (uses "{valid_letters}" units).')
    multiplier = -1 if negative else 1
    return DateTimeDelta(years=values.get('y', 0) * multiplier,
                         months=values.get('m', 0) * multiplier,
                         weeks=values.get('w', 0) * multiplier,
                         days=values.get('d', 0) * multiplier,
                         hours=values.get('H', 0) * multiplier,
                         minutes=values.get('M', 0) * multiplier,
                         seconds=values.get('S', 0) * multiplier)


def apply_date_time_delta_string(delta_string: str | None,
                                 negative: bool = False,
                                 start_time: struct_time = None,
                                 default_letter: str = None,
                                 date_only: bool = False,
                                 time_only: bool = False,
                                 ) -> struct_time:
    """Parse a time delta and apply to the current time or a specific one.

    See parse_date_time_delta() for more information about delta strings.

    Args:
        delta_string: time delta specification
        negative: apply in a reverse time direction if True
        start_time: start time as time_struct (default: current time)
        default_letter: letter substituted when none provided for value
            (default: 's')
        date_only: only accept date (ymwd) values
        time_only: only accept time (HMS) values

    Returns:
        calculated time as time_struct
    """
    delta = parse_date_time_delta(delta_string,
                                  negative=negative,
                                  default_letter=default_letter,
                                  date_only=date_only,
                                  time_only=time_only)
    return apply_date_time_delta(delta, start_time=start_time)


def apply_date_time_delta(delta: DateTimeDelta,
                          start_time: struct_time = None,
                          ) -> struct_time:
    """Apply a date/time delta to the current time or a specific one.

    Args:
        delta: time delta data
        start_time: start time as time_struct (default: current time)

    Returns:
        calculated time as time_struct
    """
    if start_time is not None:
        start_datetime = datetime.datetime.fromtimestamp(mktime(start_time))
    else:
        start_datetime = datetime.datetime.now()
    result_datetime = start_datetime
    # No timedelta support for month or year. So handle them separately.
    new_month_raw = result_datetime.month + delta.months
    new_month = (new_month_raw - 1) % 12 + 1
    months_carry = (new_month_raw - 1) // 12
    new_year = result_datetime.year + delta.years + months_carry
    result_datetime = result_datetime.replace(month=new_month, year=new_year)
    result_datetime += datetime.timedelta(seconds=delta.seconds,
                                          minutes=delta.minutes,
                                          hours=delta.hours,
                                          days=delta.days,
                                          weeks=delta.weeks)
    return result_datetime.timetuple()


def parse_date_time(date_time_string: str | None,
                    quiet: bool = False,
                    ) -> struct_time | None:
    """Flexible parsing of date and or time strings.

    The format is similar to ISO in that dates are dash-separated and in y-m-d
    order. Times are colon-separated, and less significant time components may
    be omitted.

    Date years may be omitted, with it defaulting to the current year.

    The string may have just a date, just a time, or both. If both are specified
    they must be space-separated.

    Args:
        date_time_string: date/time string to parse (None is the same as empty)
        quiet: suppress errors, e.g. for unit testing

    Returns:
        date/time date as time_struct or None if parsing fails
    """
    if date_time_string is None:
        return None
    date_time_string = date_time_string.strip()
    if not date_time_string:
        return None
    parts = date_time_string.split()
    if len(parts) > 2:
        if not quiet:
            log_error(f'Too many parts in date/time string "{date_time_string}".')
        return None
    parsed_date: datetime.date | None = None
    parsed_time: datetime.time | None = None
    try:
        for part_string in parts:
            if part_string.find('-') != -1:
                if parsed_date is not None:
                    raise ValueError(f'more than one date part')
                date_parts = part_string.split('-')
                if len(date_parts) == 2:
                    # Inject the current year when there is no year.
                    date_parts.insert(0, str(localtime().tm_year))
                elif len(date_parts) == 3 and len(date_parts[0]) == 2:
                    # Lengthen a short 2 digit year.
                    date_parts[0] = str(localtime().tm_year)[:2] + date_parts[0]
                fixed_date_string = '-'.join(date_parts)
                parsed_date = datetime.date.fromisoformat(fixed_date_string)
            else:
                if parsed_time is not None:
                    raise ValueError(f'more than one time part')
                parsed_time = datetime.time.fromisoformat(part_string)
    except ValueError as exc:
        if not quiet:
            log_error(f'Bad date/time string "{date_time_string}".', exc)
        return None
    if parsed_date is None and parsed_time is None:
        return None
    if parsed_date is not None:
        if parsed_time is None:
            parsed_time = datetime.time(0, 0, 0)
    elif parsed_time is not None:
        if parsed_date is None:
            parsed_date = datetime.date.today()
    return datetime.datetime.combine(parsed_date, parsed_time).timetuple()


def parse_time_interval(interval_string: str | None) -> int | None:
    """Parse time interval with same syntax as parse_date_time_delta() accepts.

    Args:
        interval_string: HMS time interval string (handles None)

    Returns:
        delta in seconds as integer
    """
    if not interval_string:
        return None
    delta = parse_date_time_delta(interval_string, time_only=True)
    if delta is None:
        return None
    return (delta.hours * 3600) + (delta.minutes * 60) + delta.seconds


def timestamp_to_strftime_format(timestamp_format: str = None) -> str | None:
    """Convert simplified timestamp specification to strftime format string.

    Case-insensitive timestamp format strings can include the following
    components. Possible components include date/time specifiers (see list
    below) and separator characters ('.', '-', or '_'). Date/time specifiers may
    be omitted, but whichever ones are present must follow the order listed
    below. Month ('mm') is distinguished from minutes (also 'mm') by requiring
    minutes be preceded by hours ('hh').

    * yyyy - 4 digit year
    * yy - 2 digit year
    * mm - 2 digit month
    * dd - 2 digit day of the month
    * hh - 2 digit hours (00-23)
    * mm - 2 digit minutes (00-59) (only interpreted as minutes if preceded by 'hh')
    * ss - 2 digit seconds (00-59)

    Formatting options are intentionally limited so that the resulting string is
    sortable, and works with file names.

    Args:
        timestamp_format: optional timestamp format specification (default:
            'yyyymmddhhmmss')

    Returns:
        strftime format string or None if timestamp_format is bad
    """
    if timestamp_format is None:
        return TIMESTAMP_DEFAULT_STRFTIME_FORMAT
    matched = TIMESTAMP_FORMAT_REGEX.match(timestamp_format.lower())
    if matched is None:
        return None
    strftime_parts: list[str] = []
    for group in matched.groups():
        if group is not None:
            match group:
                case 'yyyy':
                    strftime_parts.append('%Y')
                case 'yy':
                    strftime_parts.append('%y')
                case 'mm':
                    # 'mm' is either month or minutes (if preceded by hours).
                    if '%H' in strftime_parts:
                        strftime_parts.append('%M')
                    else:
                        strftime_parts.append('%m')
                case 'dd':
                    strftime_parts.append('%d')
                case 'hh':
                    strftime_parts.append('%H')
                case 'ss':
                    strftime_parts.append('%S')
                case _:
                    strftime_parts.append(group)
    return ''.join(strftime_parts)


def timestamp_string(timestamp_format: str = None,
                     time_value: float | struct_time = None,
                     ) -> str:
    """Generate timestamp string based on simplified specification.

    Case-insensitive timestamp format strings can include the following
    components. Possible components include date/time specifiers (see list
    below) and separator characters ('.', '-', or '_'). Date/time specifiers may
    be omitted, but whichever ones are present must follow the order listed
    below. Month ('mm') is distinguished from minutes (also 'mm') by requiring
    minutes be preceded by hours ('hh').

    * yyyy - 4 digit year
    * yy - 2 digit year
    * mm - 2 digit month
    * dd - 2 digit day of the month
    * hh - 2 digit hours (00-23)
    * mm - 2 digit minutes (00-59) (only interpreted as minutes if preceded by 'hh')
    * ss - 2 digit seconds (00-59)

    Formatting options are intentionally limited so that the resulting string is
    sortable, and works with file names.

    Args:
        timestamp_format: optional timestamp format specification (default:
            'yyyymmddhhmmss')
        time_value: optional time value as float or struct_time (default:
            current time)

    Returns:
        timestamp string
    """
    strftime_format = timestamp_to_strftime_format(timestamp_format)
    if strftime_format is None:
        log_error(f'Bad timestamp string format: {timestamp_format}')
        return ''
    if time_value is None:
        time_value = localtime()
    elif isinstance(time_value, float):
        time_value = localtime(time_value)
    return strftime(strftime_format, time_value)
