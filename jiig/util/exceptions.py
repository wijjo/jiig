# Copyright (C) 2020-2022, Steven Cooper
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

"""
Python exception utilities.
"""

import os
import sys
import traceback
from dataclasses import dataclass
from typing import Text, List, Optional


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


def get_exception_stack(skip_external_frames: bool = False,
                        skip_non_source_frames: bool = False,
                        string_file_name: str = None,
                        skip_frame_count: int = None,
                        ) -> ExceptionStack:
    """
    Get exception stack as list.

    By default it tries to minimize the stack frames returned to leave out
    non-file frames, e.g. due to exec()'d code, and frames outside of the top
    level application frame.

    Non-source frames may be skipped in order to clean up exception stack for
    exec() or programmatic module import.

    :param skip_external_frames: exclude external non-application frames if True
    :param skip_non_source_frames: skip non-source file frames if True
    :param string_file_name: file to replace <string> in exception output for exec'd file
    :param skip_frame_count: optional number of frames to skip
    :return: stack item list
    """
    last_exc_tb = sys.exc_info()[2]
    # Get trimmed list of raw traceback items.
    if last_exc_tb is not None:
        tb_items = traceback.extract_tb(last_exc_tb)
        if skip_frame_count:
            tb_items = tb_items[skip_frame_count:]
    else:
        tb_items = []
    # Pass 1: Build initial stack list from extracted traceback, and optionally
    # remove non-source file frames (if skip_non_source_frames is True).
    stack_items = [
        ExceptionStackItem(tb_item.filename, tb_item.lineno, tb_item.line, tb_item.name)
        for tb_item in tb_items
        if not skip_non_source_frames or os.path.exists(tb_item.filename)
    ]
    # Pass 2: Optionally replace first contiguous block of "<string>" file names
    # with string_file_name (if string_file_name is specified).
    if stack_items and string_file_name:
        initial_non_file_frame = False
        for stack_item in stack_items:
            if os.path.exists(stack_item.path):
                if not initial_non_file_frame:
                    break
                initial_non_file_frame = False
                continue
            if stack_item.path != '<string>':
                break
            stack_item.path = string_file_name
    # Pass 3: Optionally trim frames not in top level package (if
    # skip_external_frames is True).
    package: Optional[Package] = None
    if stack_items and skip_external_frames:
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


def format_exception(exc: Exception,
                     label: Text = None,
                     skip_frame_count: int = 0,
                     show_exception_location: bool = False,
                     ) -> Text:
    """
    Format exception text.

    :param exc: the exception to format
    :param label: preamble for exception message
    :param skip_frame_count: number of stack frames to skip
    :param show_exception_location: add exception location to output if True
    :return: text string for exception
    """
    parts = []
    if label:
        parts.append(label)
    if show_exception_location:
        stack = get_exception_stack(skip_frame_count=skip_frame_count)
        if stack:
            item = stack.items[0]
            parts.append(f'{os.path.basename(item.path)}.{item.line}')
    parts.append(exc.__class__.__name__)
    parts.append(str(exc))
    return ': '.join(parts)
