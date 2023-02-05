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

"""
Python exception utilities.
"""

import os
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Package:
    """Python package data."""
    name: str
    folder: Path


def package_for_path(path: str | Path) -> Package:
    """
    Provide a package name based on a path.

    Returns an empty string if not enclosed in a package.

    :param path: path to convert to a package
    :return: package data based on path
    """
    if not isinstance(path, Path):
        path = Path(path)
    folder = path if path.is_dir() else path.parent
    names: list[str] = []
    while (folder / '__init__.py').exists():
        names.insert(0, folder.name)
        new_folder = folder.parent
        if new_folder == folder:
            break
        folder = new_folder
    return Package('.'.join(names), folder)


@dataclass
class ExceptionStackItem:
    path: str
    line: int
    text: str
    scope: str

    @property
    def location_string(self) -> str:
        scope = '' if self.scope == '<module>' else f'[{self.scope}]'
        return f'{self.path}.{self.line}{scope}'


@dataclass
class ExceptionStack:
    items: list[ExceptionStackItem]
    package_path: str | None


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
    package: Package | None = None
    if stack_items and skip_external_frames:
        for item_idx, item in enumerate(stack_items):
            item_package = package_for_path(item.path)
            if package is None:
                package = item_package
            else:
                if item_package.name != package.name:
                    stack_items = stack_items[:item_idx]
                    break
    return ExceptionStack(stack_items, str(package.folder) if package else None)


def format_exception(exc: Exception,
                     label: str = None,
                     skip_frame_count: int = 0,
                     show_exception_location: bool = False,
                     ) -> str:
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
    parts.append(f'exception[{exc.__class__.__name__}]')
    parts.append(str(exc))
    return ': '.join(parts)
