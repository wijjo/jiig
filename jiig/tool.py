# Copyright (C) 2021-2023, Steven Cooper
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

"""Tool specification classes."""

import os
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Self

from .constants import (
    DEFAULT_ALIASES_PATH,
    DEFAULT_BUILD_FOLDER,
    DEFAULT_DOC_FOLDER,
    DEFAULT_TEST_FOLDER,
    JIIG_VENV_ROOT,
)
from .task import TaskTree
from .types import (
    ToolMetadata,
    ToolPaths,
)
from .util.log import log_warning
from .util.options import OPTIONS
from .util.python import symbols_to_dataclass


@dataclass
class ToolOptions:
    """Boolean options governing tool behavior."""

    disable_alias: bool = False
    """Disable alias feature if True."""

    disable_help: bool = False
    """Disable help feature if True."""

    disable_debug: bool = False
    """Disable debug option if True."""

    disable_dry_run: bool = False
    """Disable dry run option if True."""

    disable_verbose: bool = False
    """Disable verbose option if True."""

    enable_pause: bool = False
    """Enable pause option if True."""

    enable_keep_files: bool = False
    """Enable keep files option if True."""

    hide_builtin_tasks: bool = False
    """Hide tasks like help, alias, venv, etc. from help."""

    is_jiig: bool = False
    """Running the Jiig tool if True."""

    @classmethod
    def from_raw_data(cls, raw_tool_options: Any) -> Self:
        """Convert raw data to tool options object.

        Args:
            raw_tool_options: raw input data

        Returns:
            tool options object
        """
        if raw_tool_options is None:
            return ToolOptions()
        if not isinstance(raw_tool_options, dict):
            log_warning('Ignoring tool_options, because it is not a dictionary.')
            return ToolOptions()
        return symbols_to_dataclass(raw_tool_options, ToolOptions)


@dataclass
class ToolCustomizations:
    """Tool customization data."""

    runtime: type | str | ModuleType | None
    """Custom runtime context module or class reference (Runtime subclass)."""

    driver: type | str | ModuleType | None
    """Driver class reference."""


class Tool:
    """Tool data."""

    def __init__(self,
                 meta: ToolMetadata,
                 task_tree: TaskTree,
                 options: ToolOptions = None,
                 custom: ToolCustomizations = None,
                 paths: ToolPaths = None,
                 extra_symbols: dict[str, Any] = None,
                 global_option_names: list[str] = None,
                 ):
        """Tool constructor.

        Args:
            meta: runtime metadata
            task_tree: task specification tree
            options: tool runtime options
            custom: tool customizations
            paths: various filesystem paths
            extra_symbols: optional extra symbols for unknown keys
            global_option_names: global option names, e.g. used by CLI driver
                for parsing
        """
        self.meta = meta
        self.task_tree = task_tree
        self.options = options or ToolOptions()
        self.custom = custom or ToolCustomizations(None, None)
        self.paths = paths or ToolPaths(
            libraries=[],
            venv=JIIG_VENV_ROOT / meta.tool_name,
            aliases=DEFAULT_ALIASES_PATH,
            build=DEFAULT_BUILD_FOLDER,
            doc=DEFAULT_DOC_FOLDER,
            test=DEFAULT_TEST_FOLDER,
        )
        self.extra_symbols = extra_symbols or {}
        self.global_option_names = global_option_names or []
        if not self.options.disable_debug:
            self.global_option_names.append('debug')
        if not self.options.disable_dry_run:
            self.global_option_names.append('dry_run')
        if not self.options.disable_verbose:
            self.global_option_names.append('verbose')
        if self.options.enable_pause:
            self.global_option_names.append('pause')
        if self.options.enable_keep_files:
            self.global_option_names.append('keep_files')

    def apply_options(self, runtime_data: object):
        """Apply options specified as runtime data attributes.

        Args:
            runtime_data: object with options as attributes
        """
        # Update global util options so that they are in effect upon returning.
        if not self.options.disable_debug and getattr(runtime_data, 'DEBUG'):
            OPTIONS.set_debug(True)
        if not self.options.disable_dry_run and getattr(runtime_data, 'DRY_RUN'):
            OPTIONS.set_dry_run(True)
        if not self.options.disable_verbose and getattr(runtime_data, 'VERBOSE'):
            OPTIONS.set_verbose(True)
        if self.options.enable_pause and getattr(runtime_data, 'PAUSE'):
            OPTIONS.set_pause(True)
        if self.options.enable_keep_files and getattr(runtime_data, 'KEEP_FILES'):
            OPTIONS.set_keep_files(True)

    # noinspection PyListCreation
    def __str__(self) -> str:
        blocks: list[str] = []
        blocks.append('===== Tool =====')
        blocks.append(str(self.meta))
        blocks.append(str(self.options))
        blocks.append(str(self.paths))
        blocks.append(str(self.custom))
        blocks.append(f'extra_symbols: {self.extra_symbols}')
        blocks.append(f'global_option_names: {self.global_option_names}')
        blocks.append(f'task_tree: (tasks={len(self.task_tree.tasks)}'
                      f' groups={len(self.task_tree.groups)})')
        blocks.append('================')
        return os.linesep.join(blocks)
