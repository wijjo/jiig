"""
General-purpose (independent) utilities.

Make sure that any other utility module can import this module without circular
import references. I.e. DO NOT import other utility modules here.

To handle errors independently, avoid functions like console.log_error(), and
either throw an exception or provide an informative return value.
"""

import os
import sys
import traceback
from dataclasses import dataclass
from subprocess import run
from textwrap import wrap
from typing import Iterable, Any, Text, Iterator, List, \
    Optional, Tuple, Sequence, Callable, Union, Dict

from .options import OPTIONS


class MetaAttrDict(type):
    """
    Meta-class for creating dictionary-based classes with attribute style access.

    This can be used directly for user-created attribute dictionaries, but for
    convenience, all combinations of options are wrapped in canned AttrDict...
    classes below.
    """

    # noinspection PyUnresolvedReferences
    def __new__(mcs, mcs_name, bases, namespace, **kwargs):
        """
        Create a new attribute-dictionary class.

        :param mcs_name: class name
        :param bases: base classes
        :param namespace: class attributes
        :param kwargs: keyword arguments with options from class declaration
        """

        # Safety check that the class inherits from dict.
        if dict not in bases:
            raise TypeError(f'Class {mcs_name} is not based on dict.')

        # Create the class before mixing in attribute access methods below.
        new_class = super(MetaAttrDict, mcs).__new__(mcs, mcs_name, bases, namespace)

        # Attribute read access with no_defaults=True raises AttributeError for non-existent key.
        if kwargs.get('no_defaults', False):
            def getattr_stub(self, name):
                try:
                    return self[name]
                except KeyError:
                    raise AttributeError(f"Attempt to read missing attribute '{name}' in {mcs_name}.")
            setattr(new_class, '__getattr__', getattr_stub)

        # Attribute read access otherwise uses get() to return value or None.
        else:
            setattr(new_class, '__getattr__', new_class.get)

        # Attribute write access attempt with read_only=True raises AttributeError.
        if kwargs.get('read_only', False):
            # noinspection PyUnusedLocal
            def setattr_stub(self, name, value):
                raise AttributeError(f"Attempt to write to attribute '{name}' in read-only {mcs_name}.")
            setattr(new_class, '__setattr__', setattr_stub)

        # Attribute write access otherwise performs dictionary assignment.
        else:
            setattr(new_class, '__setattr__', new_class.__setitem__)

        return new_class


class AttrDict(dict, metaclass=MetaAttrDict):
    """Dictionary wrapper with attribute-based item access."""
    pass


class AttrDictReadOnly(dict, metaclass=MetaAttrDict, read_only=True):
    """Dictionary wrapper with read-only attribute-based item access."""
    pass


class AttrDictNoDefaults(dict, metaclass=MetaAttrDict, no_defaults=True):
    """
    Dictionary wrapper with attribute-based item access.

    Raises AttributeError when attempting to read a non-existent name.
    """
    pass


class AttrDictNoDefaultsReadOnly(dict, metaclass=MetaAttrDict, no_defaults=True, read_only=True):
    """
    Dictionary wrapper with read-only attribute-based item access.

    Raises AttributeError when attempting to read a non-existent name.
    """
    pass


@dataclass
class DefaultValue:
    value: Any


def make_list(value: Any, strings: bool = False, allow_none: bool = False) -> Optional[List]:
    """
    Coerce a sequence or non-sequence to a list.

    :param value: item to make into a list
    :param strings: convert to text strings if True
    :param allow_none: return None if value is None if True, otherwise empty list
    :return: resulting list or None if value is None
    """
    def _fix(items: List) -> List:
        if not strings:
            return items
        return [str(item) for item in items]
    if value is None:
        return None if allow_none else []
    if isinstance(value, list):
        return _fix(value)
    if isinstance(value, tuple):
        return _fix(list(value))
    return _fix([value])


def make_tuple(value: Any, strings: bool = False, allow_none: bool = False) -> Optional[Tuple]:
    """
    Coerce a sequence or non-sequence to a tuple.

    :param value: item to make into a tuple
    :param strings: convert to text strings if True
    :param allow_none: return None if value is None if True, otherwise empty list
    :return: resulting tuple or None if value is None
    """
    def _fix(items: Tuple) -> Tuple:
        if not strings:
            return items
        return tuple(str(item) for item in items)
    if value is None:
        return None if allow_none else tuple()
    if isinstance(value, tuple):
        return _fix(value)
    if isinstance(value, list):
        return _fix(tuple(value))
    return _fix(tuple([value]))


HUMAN_BINARY_UNITS = ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
HUMAN_DECIMAL_UNITS = ['KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']


def human_byte_count(byte_count: float,
                     unit_format: Optional[Text],
                     ) -> Tuple[float, Text]:
    """
    Adjust raw byte count to add appropriate unit.

    unit_format values:
      b: binary/1024-based KiB, MiB, etc.
      d: decimal/1000-based KB, MB, etc.
      other: returns error text instead of unit

    :param byte_count: input byte count
    :param unit_format: 'd' for KB/MB/..., 'b' for KiB/MiB/..., or bytes if None
    :return: (adjusted byte count, unit string) tuple
    """
    byte_count = float(byte_count)      # cya
    if unit_format is None:
        return byte_count, ''
    unit_format = unit_format.lower()
    if unit_format not in ['b', 'd']:
        return byte_count, f'(unit format "{unit_format}"?)'
    if unit_format.lower() == 'b':
        divisor = 1024
        unit_strings = HUMAN_BINARY_UNITS
    else:
        divisor = 1000
        unit_strings = HUMAN_DECIMAL_UNITS
    adjusted_quantity = byte_count
    for unit_idx in range(len(unit_strings)):
        if adjusted_quantity < divisor:
            if unit_idx == 0:
                return float(byte_count), ''
            return adjusted_quantity, unit_strings[unit_idx - 1]
        adjusted_quantity /= divisor
    return adjusted_quantity, unit_strings[-1]


def format_human_byte_count(byte_count: int,
                            unit_format: Text = None,
                            decimal_places: int = 1
                            ) -> Text:
    """
    Format byte count for human consumption using unit abbreviations.

    unit_format values:
      b: binary/1024-based KiB, MiB, etc.
      d: decimal/1000-based KB, MB, etc.
      other: returns error text instead of unit

    :param byte_count: number of bytes
    :param unit_format: 'd' for KB/MB/..., 'b' for KiB/MiB/..., or bytes if None
    :param decimal_places: number of decimal places (default=1 if unit_format specified)
    :return: formatted string with applied unit abbreviation
    """
    return ('{:0.%df}{}' % (decimal_places or 1)).format(
        *human_byte_count(byte_count, unit_format))


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
        left_separators_width = len(OPTIONS.column_separator) * (len(widths) - 1)
        last_width = max_width - left_separators_width - left_columns_width
        if last_width < 20:
            last_width = None

    if row_count > 0 or display_empty:

        format_strings = ['{:%d}' % w for w in widths[:-1]]
        format_strings.append('{}')
        format_string = OPTIONS.column_separator.join(format_strings)
        if headers is not None:
            yield format_string.format(*_get_strings(headers, padded=True))
            yield OPTIONS.column_separator.join(['-' * width for width in widths])

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


def format_exception(exc: Exception,
                     label: Text = None,
                     skip_stack_levels: int = 0,
                     show_exception_location: bool = False,
                     ) -> Text:
    """
    Format exception text.

    :param exc: the exception to format
    :param label: preamble for exception message
    :param skip_stack_levels: number of stack levels to skip
    :param show_exception_location: add exception location to output if True
    :return: text string for exception
    """
    parts = []
    if label:
        parts.append(label)
    if show_exception_location:
        stack = traceback.extract_tb(sys.exc_info()[2])
        if len(stack) > skip_stack_levels:
            file, line, _function, _source = stack[skip_stack_levels]
            parts.append(f'{os.path.basename(file)}.{line}')
    parts.append(exc.__class__.__name__)
    parts.append(str(exc))
    return ': '.join(parts)


def format_message_lines(text: Any, *args, **kwargs) -> Iterator[Text]:
    """
    Generate message line(s) and indented lines for relevant keyword data.

    Keywords:
    - tag: special prefix string for all lines with an uppercase tag string
    - sub_tag: string to appear in square brackets next to the tag
    - exec_file_name: file name to replace '<string>' exception location name

    :param text: primary text
    :param args: positional arguments to format as data lines
    :param kwargs: keyword arguments to format as data lines
    :return: line iterator
    """
    tag = kwargs.pop('tag', None)
    sub_tag = kwargs.pop('sub_tag', None)
    exec_file_name = kwargs.pop('exec_file_name', None)

    def _generate_exception_lines(exc: Exception) -> Iterator[Text]:
        exc_lines = format_exception(exc).split(os.linesep)
        if exc_lines:
            exc_text = f'exception: {exc_lines[0]}'
            if exec_file_name:
                exc_text = exc_text.replace('<string>', exec_file_name)
            yield exc_text
            for exc_line in exc_lines[1:]:
                yield exc_line

    def _generate_raw_lines():
        if text:
            if isinstance(text, (list, tuple)):
                for seq_line in text:
                    yield seq_line
            else:
                yield str(text)
        for value in args:
            if isinstance(value, Exception):
                for exc_value in _generate_exception_lines(value):
                    yield f'{OPTIONS.message_indent}{exc_value}'
            else:
                yield f'{OPTIONS.message_indent}{value}'
        for key, value in kwargs.items():
            if isinstance(value, (list, tuple)):
                for idx, sub_value in enumerate(value):
                    if isinstance(sub_value, Exception):
                        sub_value = format_exception(sub_value)
                    yield f'{OPTIONS.message_indent}{key}[{idx + 1}]: {sub_value}'
            else:
                if isinstance(value, Exception):
                    value = {format_exception(value)}
                yield f'{OPTIONS.message_indent}{key}: {value}'

    if not tag:
        for line in _generate_raw_lines():
            yield line
    else:
        if not sub_tag:
            full_tag = tag.upper()
        else:
            full_tag = f'{tag.upper()}[{sub_tag}]'
        for line in _generate_raw_lines():
            yield f'{full_tag}: {line}'


def format_message_block(message: Any, *args, **kwargs) -> Text:
    """
    Format multi-line message text with positional and keyword arguments.

    "tag" is a special string keyword argument that prefixes all lines with an
    uppercase tag string.

    :param message: primary message text
    :param args: positional arguments to format as data lines
    :param kwargs: keyword arguments to format as data lines
    :return: formatted multiline message text block
    """
    return os.linesep.join(format_message_lines(message, *args, **kwargs))


def plural(noun: Text, countable: Any):
    """
    Simplistic text pluralization.

    If `countable` length is one:

    - Return unchanged.

    Otherwise if countable length is zero or greater than one:

    - If it ends in 'y', return with ending 'y' replaced by 'ies'.
    - Otherwise return with 's' appended.

    ** No other irregular pluralization cases are handled. Please be aware of
    the input, and how the simplistic algorithm works for it (or not). **

    :param noun: noun to pluralize as needed
    :param countable: item with a length that determines if it is pluralized
    :return: possibly-pluralized noun
    """
    try:
        if len(countable) != 1:
            if noun.endswith('y'):
                return f'{noun[:-1]}ies'
            return f'{noun}s'
    except TypeError:
        pass
    return noun


def binary_search(sequence: Sequence,
                  value: Any,
                  key: Callable[[Any], Any] = None,
                  ) -> Optional[Any]:
    """
    Perform binary search on ordered sequence.

    Based on standard bisect library, but cloned and adapted code for arbitrary
    item types and an optional key() function. Unlike find(), it returns
    the found item or None, instead of a position or -1.

    :param sequence: ordered item sequence to search
    :param value: value to search for
    :param key: optional key function a la sort() to return item key value
    :return: found item or None if not found
    """
    # "Borrowed" and adapted code from bisect.bisect_left().
    lo = 0
    hi = len(sequence)
    while lo < hi:
        mid = (lo + hi) // 2
        # Use __lt__ to match the logic in list.sort() and in heapq
        item = sequence[mid]
        if key is None:
            key_value = item
        else:
            key_value = key(item)
        if key_value < value:
            lo = mid + 1
        else:
            hi = mid
    if lo == len(sequence):
        return None
    return sequence[lo]


def filter_dict(function: Callable[[Any, Any], bool],
                input_data: Union[Dict, Sequence[Tuple[Any, Any]]],
                ) -> dict:
    """
    Apply filter function to a dictionary or pair sequence.

    :param function: function passed key and value arguments and returns True to keep
    :param input_data: input dictionary or pair sequence
    :return: filtered output dictionary
    """
    # If input data is not a dictionary assume it's a pair sequence.
    return dict(
        filter(
            lambda kv: function(kv[0], kv[1]),
            input_data.items() if isinstance(input_data, dict) else input_data
        )
    )


def fit_text(text: Text,
             width: int,
             placeholder: Text = '...',
             pad: Text = None,
             front: bool = False,
             ):
    """
    Truncate text in various ways.

    Note that this is not word-sensitive, like textwrap.shorten().

    :param text: text to truncate
    :param width: width to truncate to
    :param placeholder: placeholder string (default: '...')
    :param pad: character to use for padding a string shorter than width (default: not padded)
    :param front: truncate from start of string if True
    :return: potentially-truncated or padded text
    """
    placeholder_width = len(placeholder)
    text_width = len(text)
    excess_width = text_width - width
    if excess_width <= 0:
        if pad is None or excess_width == 0:
            return text
        if front:
            return ''.join([pad * (-excess_width), text])
        return ''.join([text, pad * (-excess_width)])
    if front:
        return ''.join([placeholder, text[excess_width + placeholder_width:]])
    else:
        return ''.join([text[:-(excess_width + placeholder_width)], placeholder])


@dataclass
class ExceptionStackItem:
    path: Text
    line: int
    text: Text
    scope: Text

    @property
    def location_string(self) -> Text:
        scope = '' if self.scope == '<module>' else f'[{self.scope}]'
        return f'{self.path}.{self.line}{scope}'


@dataclass
class ExceptionStack:
    items: List[ExceptionStackItem]
    package_path: Optional[Text]


def get_exception_stack(exclude_external_frames: bool = False,
                        exclude_exec_frames: bool = False,
                        exec_file_name: str = None,
                        skip: int = None,
                        ) -> ExceptionStack:
    """
    Get exception stack as list.

    By default it tries to minimize the stack frames returned to leave out
    non-file frames, e.g. due to exec()'d code, and frames outside of the top
    level application frame.

    :param exclude_external_frames: exclude external non-application frames if True
    :param exclude_exec_frames: exclude exec() (non-source file) frames if True
    :param exec_file_name: file to replace <string> in exception output for exec'd file
    :param skip: optional number of frames to skip
    :return: stack item list
    """
    last_exc_tb = sys.exc_info()[2]
    # Get trimmed list of raw traceback items.
    if last_exc_tb is not None:
        tb_items = traceback.extract_tb(last_exc_tb)
        if skip:
            tb_items = tb_items[skip:]
    else:
        tb_items = []
    # Trim or tweak first non-source file frame, e.g. to hide a string exec().?
    stack_items = []
    initial_frame = exclude_exec_frames or bool(exec_file_name)
    for item_idx, tb_item in enumerate(tb_items):
        path = tb_item.filename
        if initial_frame:
            if os.path.exists(tb_item.filename):
                initial_frame = False
            else:
                if exec_file_name:
                    path = exec_file_name
                else:
                    continue
        stack_items.append(ExceptionStackItem(path, tb_item.lineno, tb_item.line, tb_item.name))
    # Trim external frames, i.e. ones that are not in the top level package?
    package: Optional[Package] = None
    if stack_items and exclude_external_frames:
        for item_idx, item in enumerate(stack_items):
            item_package = package_for_path(item.path)
            if package is None:
                package = item_package
            else:
                if item_package.name != package.name:
                    stack_items = stack_items[:item_idx]
                    break
    return ExceptionStack(stack_items,
                          package.folder if package is not None else None)


@dataclass
class Package:
    name: Text
    folder: Text


def package_for_path(path: Text) -> Package:
    """
    Provide a package name based on a path.

    Returns an empty string if not enclosed in a package.

    :param path: path to convert to a package
    :return: package data based on path
    """
    folder = path if os.path.isdir(path) else os.path.dirname(path)
    names: List[Text] = []
    while os.path.exists(os.path.join(folder, '__init__.py')):
        names.insert(0, os.path.basename(folder))
        new_folder = os.path.dirname(folder)
        if new_folder == folder:
            break
        folder = new_folder
    return Package('.'.join(names), folder)


def get_client_name() -> str:
    client = run('uname -n', shell=True, capture_output=True, encoding='utf-8').stdout.strip()
    if client.endswith('.local_command'):
        client = client[:-6]
    return client


class BlockSplitter:
    def __init__(self, *blocks: str, indent: int = None, double_spaced: bool = False):
        self.lines: List[str] = []
        self.indent = indent
        self.double_spaced = double_spaced
        self.found_indent: Optional[int] = None
        self._trimmed_lines: Optional[List[str]] = None
        for block in blocks:
            self.add_block(block)

    def add_block(self, block: str):
        if self.lines and self.double_spaced:
            self.lines.append('')
        have_empty = False
        have_non_empty = False
        for line in block.split(os.linesep):
            line = line.rstrip()
            line_length = len(line)
            indent = line_length - len(line.lstrip())
            if indent == line_length:
                have_empty = have_non_empty
            else:
                have_non_empty = True
                if have_empty:
                    self.lines.append('')
                    have_empty = False
                self.lines.append(line)
                if self.found_indent is None or indent < self.found_indent:
                    self.found_indent = indent

    @property
    def trimmed_lines(self) -> List[str]:
        indent = ' ' * self.indent if self.indent else ''
        if self._trimmed_lines is None:
            if self.found_indent:
                self._trimmed_lines = [indent + line[self.found_indent:] for line in self.lines]
            else:
                self._trimmed_lines = [indent + line for line in self.lines]
        return self._trimmed_lines


def trim_text_blocks(*blocks: str,
                     indent: int = None,
                     keep_indent: bool = False,
                     double_spaced: bool = False,
                     ) -> List[str]:
    splitter = BlockSplitter(*blocks, indent=indent, double_spaced=double_spaced)
    if keep_indent:
        return splitter.lines
    return splitter.trimmed_lines


def trim_text_block(block: str,
                    indent: int = None,
                    keep_indent: bool = False,
                    double_spaced: bool = False,
                    ) -> str:
    return os.linesep.join(trim_text_blocks(block,
                                            indent=indent,
                                            keep_indent=keep_indent,
                                            double_spaced=double_spaced))
