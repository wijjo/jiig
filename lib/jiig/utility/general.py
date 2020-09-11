"""General utilities."""
from typing import Iterable, Any, Text, Iterator, List, Optional


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


def format_byte_count(byte_count: int,
                      decimal_places: int = None,
                      binary_units: bool = False) -> Text:
    """
    Format byte count string using BINARY_BYTE_COUNT_UNITS abbreviations

    :param byte_count: number of bytes
    :param decimal_places: number of decimal places
    :param binary_units: use KiB, MiB, etc. 1024-based units vs. KB, MB, etc. 1000-based units
    :return: formatted string with applied unit abbreviation
    """
    if binary_units:
        units = BINARY_BYTE_COUNT_UNITS
        factor = 1024
    else:
        units = DECIMAL_BYTE_COUNT_UNITS
        factor = 1000
    adjusted_quantity = float(byte_count)
    format_string = '{:0.%df}' % (decimal_places or 0)
    parts = []
    for unit_idx in range(len(units)):
        if adjusted_quantity < factor:
            parts.append(format_string.format(adjusted_quantity))
            if unit_idx > 0:
                parts.append(units[unit_idx - 1])
            break
        adjusted_quantity /= factor
    else:
        parts.extend([format_string.format(adjusted_quantity), units[-1]])
    return ' '.join(parts)
