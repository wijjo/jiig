"""General utilities."""

from textwrap import wrap
from typing import Iterable, Any, Text, Iterator, List, Optional, Tuple

from .console import log_error


class AttrDict(dict):

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value


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


def make_tuple(value: Any, strings: bool = False) -> Optional[Tuple]:
    """
    Coerce a sequence or non-sequence to a tuple.

    :param value: item to make into a tuple
    :param strings: convert to text strings if True
    :return: resulting tuple or None if value is None
    """
    def _fix(items: Tuple) -> Tuple:
        if not strings:
            return items
        return tuple(str(item) for item in items)
    if isinstance(value, tuple):
        return _fix(value)
    if isinstance(value, list):
        return _fix(tuple(value))
    return _fix(tuple([value]))


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


TABLE_COLUMN_SEPARATOR = '  '


def format_table(*rows: Iterable[Any],
                 headers: Iterable[Text] = None,
                 formats: Iterable[Text] = None,
                 display_empty: bool = False,
                 max_width: int = None
                 ) -> Iterator[Text]:
    """
    Generate tabular output from input rows with optional headings.

    :param rows: row data sequences
    :param headers: column header strings
    :param formats: column format strings
    :param display_empty: display headers when there are no rows
    :param max_width: optional maximum full line width used for wrapping the
                      last column as needed
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

    # Calculate wrapping width for last column.
    # Disable wrapping if it doesn't fit well.
    last_width: Optional[int] = None
    if max_width is not None:
        left_columns_width = sum(widths[:-1])
        left_separators_width = len(TABLE_COLUMN_SEPARATOR) * (len(widths) - 1)
        last_width = max_width - left_separators_width - left_columns_width
        if last_width < 20:
            last_width = None

    if row_count > 0 or display_empty:

        format_strings = ['{:%d}' % w for w in widths[:-1]]
        format_strings.append('{}')
        format_string = TABLE_COLUMN_SEPARATOR.join(format_strings)
        if headers is not None:
            yield format_string.format(*_get_strings(headers, padded=True))
            yield TABLE_COLUMN_SEPARATOR.join(['-' * width for width in widths])

        for row in rows:
            if last_width is None:
                yield format_string.format(*_get_strings(row, padded=True))
            else:
                column_strings = list(_get_strings(row, padded=True))
                if len(column_strings[-1]) <= last_width:
                    yield format_string.format(*column_strings)
                else:
                    partial_last_column_lines = wrap(column_strings[-1], width=last_width)
                    for idx, partial_last_column_line in enumerate(partial_last_column_lines):
                        column_strings[-1] = partial_last_column_line
                        yield format_string.format(*column_strings)
                        if idx == 0:
                            column_strings = [''] * len(widths)
