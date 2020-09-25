"""Jiig date/time utilities."""

import datetime
import time
from dataclasses import dataclass
from typing import Optional, Text, Dict

from jiig.utility.console import log_error, log_warning

DATE_DELTA_LETTERS = 'ymwd'
TIME_DELTA_LETTERS = 'HMS'
DATE_TIME_DELTA_LETTERS = DATE_DELTA_LETTERS + TIME_DELTA_LETTERS


@dataclass
class DateTimeDelta:
    years: int
    months: int
    weeks: int
    days: int
    hours: int
    minutes: int
    seconds: int


def parse_date_time_delta(delta_string: Optional[Text],
                          negative: bool = False,
                          default_letter: Text = None,
                          date_only: bool = False,
                          time_only: bool = False,
                          ) -> DateTimeDelta:
    """
    Parse a time delta and convert to a DateTimeDelta object.

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

    :param delta_string: time delta specification
    :param negative: apply in a reverse time direction if True
    :param default_letter: letter substituted when none provided for value (default: 's')
    :param date_only: only accept date (ymwd) values
    :param time_only: only accept time (HMS) values
    :return: DateTimeDelta object
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
    values: Dict[Text, int] = {}
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
                if letter in DATE_TIME_DELTA_LETTERS:
                    if value is not None:
                        if letter in values:
                            values[letter] += value
                        else:
                            values[letter] = value
                else:
                    log_warning(f'Ignoring bad{label} delta specification part "{part}".')
    multiplier = -1 if negative else 1
    return DateTimeDelta(years=values.get('y', 0) * multiplier,
                         months=values.get('m', 0) * multiplier,
                         weeks=values.get('w', 0) * multiplier,
                         days=values.get('d', 0) * multiplier,
                         hours=values.get('H', 0) * multiplier,
                         minutes=values.get('M', 0) * multiplier,
                         seconds=values.get('S', 0) * multiplier)


def apply_date_time_delta_string(delta_string: Optional[Text],
                                 negative: bool = False,
                                 start_time: time.struct_time = None,
                                 default_letter: Text = None,
                                 date_only: bool = False,
                                 time_only: bool = False,
                                 ) -> time.struct_time:
    """
    Parse a time delta and apply to the current time or a specific one.

    See parse_date_time_delta() for more information about delta strings.

    :param delta_string: time delta specification
    :param negative: apply in a reverse time direction if True
    :param start_time: start time as time_struct (default: current time)
    :param default_letter: letter substituted when none provided for value (default: 's')
    :param date_only: only accept date (ymwd) values
    :param time_only: only accept time (HMS) values
    :return: calculated time as time_struct
    """
    delta = parse_date_time_delta(delta_string,
                                  negative=negative,
                                  default_letter=default_letter,
                                  date_only=date_only,
                                  time_only=time_only)
    return apply_date_time_delta(delta, start_time=start_time)


def apply_date_time_delta(delta: DateTimeDelta,
                          start_time: time.struct_time = None,
                          ) -> time.struct_time:
    """
    Apply a date/time delta to the current time or a specific one.

    :param delta: time delta data
    :param start_time: start time as time_struct (default: current time)
    :return: calculated time as time_struct
    """
    if start_time is not None:
        start_datetime = datetime.datetime.fromtimestamp(time.mktime(start_time))
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


def parse_date_time(date_time_string: Optional[Text],
                    quiet: bool = False,
                    ) -> Optional[time.struct_time]:
    """
    Flexible parsing of date and or time strings.

    The format is similar to ISO in that dates are dash-separated and in y-m-d
    order. Times are colon-separated, and less significant time components may
    be omitted.

    Date years may be omitted, with it defaulting to the current year.

    The string may have just a date, just a time, or both. If both are specified
    they must be space-separated.

    :param date_time_string: date/time string to parse (None is the same as empty)
    :param quiet: suppress errors, e.g. for unit testing
    :return: date/time date as time_struct or None if parsing fails
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
    parsed_date: Optional[datetime.date] = None
    parsed_time: Optional[datetime.time] = None
    try:
        for part_string in parts:
            if part_string.find('-') != -1:
                if parsed_date is not None:
                    raise ValueError(f'more than one date part')
                date_parts = part_string.split('-')
                if len(date_parts) == 2:
                    # Inject the current year when there is no year.
                    date_parts.insert(0, str(time.localtime().tm_year))
                elif len(date_parts) == 3 and len(date_parts[0]) == 2:
                    # Lengthen a short 2 digit year.
                    date_parts[0] = str(time.localtime().tm_year)[:2] + date_parts[0]
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
