"""General utilities."""

import time
from datetime import datetime, timedelta
from typing import Iterable, Any, Text, Iterator, List, Optional, Dict

from .console import log_error, log_warning


class AttrDict(dict):

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value


def format_table(*rows: Iterable[Any],
                 headers: Iterable[Text] = None,
                 formats: Iterable[Text] = None,
                 display_empty: bool = False
                 ) -> Iterator[Text]:
    """
    Generate tabular output from input rows with optional headings.

    :param rows: row data sequences
    :param headers: column header strings
    :param formats: column format strings
    :param display_empty: display headers when there are no rows
    :return: formatted line generator
    """
    widths: List[int] = []
    format_list = list(formats) if formats is not None else []

    def _get_strings(columns: Iterable[Any], padded: bool = False) -> Iterator[Text]:
        num_columns = 0
        for column_idx, column in enumerate(columns):
            if len(format_list) > column_idx:
                yield column.format(format_list[column_idx])
            else:
                yield str(column)
            num_columns += 1
        if padded:
            for pad_idx in range(len(widths) - num_columns):
                yield ''

    def _check_widths(columns: Iterable[Any]):
        for column_idx, column_string in enumerate(columns):
            column_width = len(column_string)
            if column_idx == len(widths):
                widths.append(column_width)
            elif column_width > widths[column_idx]:
                widths[column_idx] = column_width

    if headers is not None:
        _check_widths(headers)
    row_count = 0
    for row in rows:
        _check_widths(_get_strings(row))
        row_count += 1

    if row_count > 0 or display_empty:

        format_strings = ['{:%d}' % w for w in widths[:-1]]
        format_strings.append('{}')
        format_string = '  '.join(format_strings)
        if headers is not None:
            yield format_string.format(*_get_strings(headers, padded=True))
            yield '  '.join(['-' * width for width in widths])

        for row in rows:
            yield format_string.format(*_get_strings(row, padded=True))


def make_list(value: Any, strings: bool = False) -> Optional[List]:
    """
    Coerce a sequence or non-sequence to a list.

    :param value: item to make into a list
    :param strings: convert to text strings if True
    :return: resulting list or None if value is None
    """
    def _fix(items: List) -> List:
        if not strings:
            return items
        return [str(item) for item in items]
    if isinstance(value, list):
        return _fix(value)
    if isinstance(value, tuple):
        return _fix(list(value))
    return _fix([value])


BINARY_BYTE_COUNT_UNITS = ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
DECIMAL_BYTE_COUNT_UNITS = ['KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']


def _format_byte_count(byte_count: int,
                       factor: int,
                       units: List[Text],
                       decimal_places: int) -> Text:
    adjusted_quantity = float(byte_count)
    unit_format = '{value:0.%df}{unit}' % (decimal_places or 1)
    for unit_idx in range(len(units)):
        if adjusted_quantity < factor:
            if unit_idx == 0:
                return str(byte_count)
            return unit_format.format(value=adjusted_quantity, unit=units[unit_idx - 1])
        adjusted_quantity /= factor
    return unit_format.format(value=adjusted_quantity, unit=units[-1])


def format_byte_count(byte_count: int,
                      unit_format: Text = None,
                      decimal_places: int = 1
                      ) -> Text:
    """
    Format byte count string using unit abbreviations.

    Either decimal_units or binary_units must be true, or it just formats it as
    a simple integer, and decimal_places is ignored.

    KB, MB, etc. are 1000-based units. KiB, MiB, etc. are 1024-based units.

    :param byte_count: number of bytes
    :param decimal_places: number of decimal places (default=1 if unit_format specified)
    :param unit_format: 'd' for KB/MB/..., 'b' for KiB/MiB/..., or bytes if None
    :return: formatted string with applied unit abbreviation
    """
    if unit_format is not None:
        if unit_format.lower() == 'b':
            return _format_byte_count(byte_count, 1024, BINARY_BYTE_COUNT_UNITS, decimal_places)
        if unit_format.lower() == 'd':
            return _format_byte_count(byte_count, 1000, DECIMAL_BYTE_COUNT_UNITS, decimal_places)
        log_error(f'Bad format_byte_count() unit_format ({unit_format}).')
    return str(byte_count)


# noinspection SpellCheckingInspection
TIME_DELTA_LETTERS = {
    'S': 'seconds',
    'M': 'months',
    'H': 'hours',
    'd': 'days',
    'w': 'weeks',
    'm': None,      # months
    'y': None,      # years
}


def apply_time_delta_string(delta_string: Optional[Text],
                            negative: bool = False,
                            start_time: time.struct_time = None,
                            default_letter: Text = None
                            ) -> time.struct_time:
    """
    Parse a time delta and apply to the current time or a specific one.

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
    :param start_time: start time as time_struct (default: current time)
    :param default_letter: letter substituted when none provided for value (default: 's')
    :return: calculated time as time_struct
    """
    if default_letter:
        # noinspection SpellCheckingInspection
        if default_letter not in TIME_DELTA_LETTERS:
            log_error(f'Bad default letter for time delta, "{default_letter}".')
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
                if letter in TIME_DELTA_LETTERS:
                    if value is not None:
                        if letter in values:
                            values[letter] += value
                        else:
                            values[letter] = value
                else:
                    log_warning(f'Ignoring bad time delta specification part "{part}".')
    if start_time is not None:
        start_datetime = datetime.fromtimestamp(time.mktime(start_time))
    else:
        start_datetime = datetime.now()
    result_datetime = start_datetime

    # Apply deltas individual from smallest to largest to make it easier to keep
    # the result normalized.
    def _value(letter_key: Text) -> int:
        if negative:
            return -values.get(letter_key, 0)
        return values.get(letter_key, 0)

    # No timedelta support for month or year. So handle them separately.
    new_month_raw = result_datetime.month + _value('m')
    new_month = (new_month_raw - 1) % 12 + 1
    months_carry = (new_month_raw - 1) // 12
    new_year = result_datetime.year + _value('y') + months_carry
    result_datetime = result_datetime.replace(month=new_month, year=new_year)

    result_datetime += timedelta(seconds=_value('S'),
                                 minutes=_value('M'),
                                 hours=_value('H'),
                                 days=_value('d'),
                                 weeks=_value('w'))

    return result_datetime.timetuple()
