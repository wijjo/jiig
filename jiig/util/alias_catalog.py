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

"""Persistent alias management.

See README.md for the design rationale.

At a high level, this module saves, loads, and manages aliases. Related to that,
it converts back and for between short and long alias names to support scoping.
"""

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Any, Iterable

from .log import abort, log_error, log_message, log_warning
from .process import shell_command_string
from .stream import read_json_file


# JSON schema:
# {
#   <tool name>: {
#     <alias name>: {
#       'description': <description string>,
#       'command': <argument list>,
#     },
#     ...
#   },
#   ...
# }


@dataclass
class _AliasCatalogScrubber:
    """Initialize by populating an alias catalog dictionary with validated data."""
    raw_data: Any
    scrubbed_data: dict = None
    errors: int = 0
    quiet: bool = False

    def __post_init__(self):
        catalog = {}
        if isinstance(self.raw_data, dict):
            for tool_name in sorted(self.raw_data.keys()):
                tool_data = self._scrub_tool_data(tool_name, self.raw_data[tool_name])
                if tool_data:
                    catalog[tool_name] = tool_data
        else:
            self._error('Entire alias map is not a dictionary.')
        self.scrubbed_data = catalog

    def _scrub_tool_data(self, tool_name: str, tool_data: Any) -> dict | None:
        scrubbed_tool_data = {}
        if isinstance(tool_data, dict):
            for alias_name in sorted(tool_data.keys()):
                alias_data = self._scrub_alias_data(alias_name, tool_data[alias_name])
                if alias_data:
                    scrubbed_tool_data[alias_name] = alias_data
        else:
            self._error(f'Alias tool "{tool_name}" data is not a dictionary.')
        return scrubbed_tool_data or None

    def _scrub_alias_data(self, alias_name: str, alias_data: Any) -> dict | None:
        scrubbed_alias_data = {}
        if isinstance(alias_data, dict):
            command = alias_data.get('command')
            if isinstance(command, list) and command:
                description = alias_data.get('description', '(no description)')
                scrubbed_alias_data['description'] = description
                scrubbed_alias_data['command'] = command
            else:
                self._error(f'Alias "{alias_name}" "command" value is missing,'
                            f' empty, or not a list.')
        else:
            self._error(f'Alias "{alias_name}" data is not a dictionary.')
        return scrubbed_alias_data or None

    def _error(self, message: str):
        if not self.quiet:
            log_error(message)
        self.errors += 1


@dataclass
class Alias:
    """Alias data."""
    # The name is the long/fully-expanded name.
    name: str
    description: str
    command: list[str]
    _short_name: str = None

    @property
    def command_string(self) -> str:
        """Full shell command string.

        Returns:
            shell-quoted command string
        """
        return shell_command_string(*self.command)

    @property
    def short_name(self) -> str:
        """Shortened alias name.

        Returns:
            shortened alias name
        """
        if self._short_name is None:
            self._short_name = shrink_alias_name(self.name)
        return self._short_name

    @property
    def label(self) -> str:
        """Alias label.

        Returns:
            alias label
        """
        return os.path.basename(self.name)

    @property
    def path(self) -> str | None:
        """Alias folder path.

        Returns:
            alias folder path
        """
        return os.path.dirname(self.name) or None

    @property
    def short_path(self) -> str | None:
        """Shortened alias folder path.

        Returns:
            shortened alias folder path
        """
        return os.path.dirname(self.short_name) or None


def is_alias_name(name: str | Path) -> bool:
    """Check if name is an alias.

    Args:
        name: name to check

    Returns:
        True if it is an alias
    """
    # If the name is a filesystem object, then it isn't an alias.
    if Path(name).exists():
        return False
    return str(name)[0] in (os.path.sep, '.', '~')


def expand_alias_name(short_name: str,
                      checked: bool = False,
                      ) -> str | None:
    """Expand scoped alias name.

    Validation is not strict, and bad paths may be accepted.

    The current implementation is inefficient and has minimal validation.

    Args:
        short_name: short alias name to expand
        checked: abort instead of raising exception

    Returns:
        expanded name or None if it isn't a valid alias name

    Raises:
        ValueError: if the alias name is bad
    """
    def _error(text: str):
        if checked:
            abort(text)
        else:
            raise ValueError(text)
    if not short_name:
        _error('No alias name received for alias operation.')
    if not is_alias_name(short_name):
        _error(f'Alias name "{short_name}" does not start with a location,'
               f' e.g. .NAME, ~NAME, or /PATH/NAME.')
    if short_name[0] == os.path.sep:
        return short_name
    last_slash_pos = short_name.rfind(os.path.sep)
    if last_slash_pos != -1:
        # expanded real path
        full_path = os.path.realpath(os.path.expanduser(short_name[:last_slash_pos]))
        return os.path.join(full_path, short_name[last_slash_pos + 1:])
    if short_name[0] == '~':
        # ~ - user home real path
        return os.path.join(os.path.realpath(os.path.expanduser('~')), short_name[1:])
    if short_name[1] == '.':
        # .. - parent folder real path
        return os.path.join(os.path.realpath(os.path.dirname(os.getcwd())), short_name[2:])
    # . - working folder real path
    return os.path.join(os.path.realpath(os.getcwd()), short_name[1:])


def shrink_alias_name(long_name: str) -> str:
    """Shrink paths using '.', '..', or '~', whenever possible.

    The current implementation is inefficient and has minimal validation.

    Args:
        long_name: long alias name to shrink

    Returns:
        shrunken name
    """
    last_slash_pos = long_name.rfind(os.path.sep)
    if last_slash_pos == -1:
        return long_name
    path = long_name[:last_slash_pos]
    name = long_name[last_slash_pos + 1:]
    if path == os.path.realpath(os.getcwd()):
        return f'.{name}'
    if path == os.path.realpath(os.path.dirname(os.getcwd())):
        return f'..{name}'
    if path == os.path.realpath(os.path.expanduser('~')):
        return f'~{name}'
    return long_name


class AliasCatalog:
    """Manages and provides access to a tool->alias->arguments map.

    It is not quiet. I.e. it validates read and write operations and displays
    errors as appropriate.

    It can be used as a context manager for a `with` block with automatic
    flushing of changes to an aliases file.
    """

    def __init__(self, tool_name: str, catalog_path: str | Path):
        """AliasCatalog constructor.

        Args:
            tool_name: tool name
            catalog_path
        """
        self.tool_name = tool_name
        self.catalog_path = catalog_path
        if not isinstance(self.catalog_path, Path):
            self.catalog_path = Path(self.catalog_path)
        self.catalog = {}
        self.modified = False
        self.disable_saving = False
        self.sorted = False
        self.load()

    @property
    def sorted_catalog(self) -> dict:
        if not self.sorted:
            self._sort_catalog()
        return self.catalog

    def iterate_aliases(self) -> Iterator[Alias]:
        """Get all locations/aliases for current tool.

        Returns:
            Alias object iterator
        """
        if not self.sorted:
            self._sort_catalog()
        return self._iterate_aliases()

    def get_alias(self, alias_name: str) -> Alias | None:
        """Get alias by name.

        Expand optional path that may precede the name.

        Args:
            alias_name: alias name, possibly preceded by a path

        Returns:
            alias data if found or None if not
        """
        full_name = expand_alias_name(alias_name, checked=True)
        tool_alias_map = self.catalog.get(self.tool_name)
        if not tool_alias_map:
            return None
        alias_data = tool_alias_map.get(full_name)
        if not alias_data:
            return None
        return Alias(alias_name, alias_data['description'], alias_data['command'])

    def load(self):
        """Load and validate the aliases file."""
        self.disable_saving = False
        self.modified = False
        if self.catalog_path.exists():
            raw_catalog = read_json_file(self.catalog_path)
            scrubber = _AliasCatalogScrubber(raw_catalog)
            self.catalog = scrubber.scrubbed_data
            if scrubber.errors > 0:
                self.disable_saving = True
        else:
            self.catalog = {}
        self.sorted = False

    def save(self):
        """Save the aliases file."""
        if self.disable_saving:
            log_error(f'Not saving aliases to "{self.catalog_path}".',
                      f'Please correct previously-reported errors or delete the file.')
            return
        try:
            with open(self.catalog_path, 'w', encoding='utf-8') as aliases_file:
                json.dump(self.sorted_catalog, aliases_file, indent=2)
            self.modified = False
        except Exception as exc:
            abort(f'Failed to write aliases file "{self.catalog_path}".', exc)

    def create_alias(self,
                     alias_name: str,
                     command: Iterable[str],
                     description: str = None):
        """Create a new alias.

        Args:
            alias_name: name of alias to create
            command: command arguments for alias (required)
            description: description of alias, e.g. for help screen
        """
        full_name = expand_alias_name(alias_name, checked=True)
        if not list(command):
            abort(f'New alias "{alias_name}" command is empty.')
        tool_alias_map = self.catalog.get(self.tool_name)
        if tool_alias_map and full_name in tool_alias_map:
            abort(f'New alias "{alias_name}" already exists.')
        # Can't easily check the entire aliased command, so just check the task name.
        if tool_alias_map is None:
            tool_alias_map = {}
            self.catalog[self.tool_name] = tool_alias_map
        description = description if description is not None else '(no description)'
        alias_data = dict(description=description, command=command)
        tool_alias_map[full_name] = alias_data
        log_message(f'Alias "{alias_name}" created.')
        self.sorted = False
        self.modified = True

    def update_alias(self,
                     alias_name: str,
                     command: Iterable[str] = None,
                     description: str = None):
        """Update an existing alias.

        Args:
            alias_name: name of alias to update
            command: command arguments for alias (optional, or not updated)
            description: description of alias (optional, or not updated)
        """
        full_name = expand_alias_name(alias_name, checked=True)
        if command is not None and not list(command):
            abort(f'Alias "{alias_name}" command is empty.')
        tool_alias_map = self.catalog.get(self.tool_name)
        if not tool_alias_map:
            abort(f'No aliases exist.')
        existing_alias_data = tool_alias_map.get(full_name)
        if not existing_alias_data:
            abort(f'Alias "{alias_name}" does not exist.')
        updated = False
        if command is not None:
            existing_alias_data['command'] = command
            updated = True
        if description is not None:
            existing_alias_data['description'] = description
            updated = True
        if not updated:
            log_warning(f'No alias "{alias_name}" information supplied for update.')
            return
        log_message(f'Alias "{alias_name}" updated.')
        self.modified = True

    def delete_alias(self, alias_name: str):
        """Delete an alias by name after expanding any preceding path.

        Args:
            alias_name: name of alias to delete
        """
        full_name = expand_alias_name(alias_name, checked=True)
        tool_alias_map = self.catalog.get(self.tool_name)
        if not tool_alias_map:
            abort('Tool has no aliases.')
        if full_name not in tool_alias_map:
            abort(f'Alias "{alias_name}" not found for deletion.')
        del tool_alias_map[full_name]
        log_message(f'Alias "{alias_name}" deleted.')
        self.modified = True

    def rename_alias(self, alias_name: str, alias_name_new: str):
        """Rename an alias.

        Applies to all locations for alias.

        Args:
            alias_name: name of alias to rename
            alias_name_new: new target alias name
        """
        full_name = expand_alias_name(alias_name, checked=True)
        full_name_new = expand_alias_name(alias_name_new, checked=True)
        tool_alias_map = self.catalog.get(self.tool_name)
        if not tool_alias_map:
            abort('Tool has no aliases.')
        existing_alias_data = tool_alias_map.get(full_name)
        if not existing_alias_data:
            abort(f'Alias "{alias_name}" does not exist.')
        existing_alias_data_new = tool_alias_map.get(full_name_new)
        if existing_alias_data_new:
            abort(f'Alias "{alias_name_new}" already exists.')
        tool_alias_map[alias_name_new] = tool_alias_map[alias_name]
        del tool_alias_map[alias_name]
        log_message(f'Alias "{alias_name}" renamed to "{alias_name_new}".')
        self.sorted = False
        self.modified = True

    def _iterate_aliases(self, tool_name: str = None) -> Iterator[Alias]:
        """Get all locations/aliases for current or specified tool.

        Args:
            tool_name: tool name (default is current tool)

        Returns:
            Alias object iterator
        """
        tool_alias_map = self.catalog.get(tool_name or self.tool_name)
        if tool_alias_map:
            for alias_name, alias_data in tool_alias_map.items():
                yield Alias(alias_name, alias_data['description'], alias_data['command'])

    def _sort_catalog(self):
        # Sort aliases by label, followed by path.
        sorted_catalog = {}
        for tool_name in sorted(self.catalog.keys()):
            sorted_aliases = sorted(self._iterate_aliases(tool_name=tool_name),
                                    key=lambda a: (a.label, a.path or ''))
            sorted_tool_alias_map = {}
            for alias in sorted_aliases:
                alias_data = dict(description=alias.description, command=alias.command)
                sorted_tool_alias_map[alias.name] = alias_data
            sorted_catalog[tool_name] = sorted_tool_alias_map
        self.catalog = sorted_catalog
        self.sorted = True

    def __enter__(self) -> 'AliasCatalog':
        """Support construction in a `with` block."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Save on ending the `with` block if no exception occurred."""
        if exc_type is None and self.modified:
            self.save()
        return False


@contextmanager
def open_alias_catalog(tool_name: str,
                       catalog_path: str | Path,
                       ) -> Iterator[AliasCatalog]:
    """Opens an alias catalog.

    It is not quiet. I.e. it validates read and write operations and displays
    errors as appropriate.

    It can be used as a context manager for a `with` block with automatic
    flushing of changes to an aliases file.

    Args:
        tool_name: tool name for isolating applicable aliases from the catalog
        catalog_path: path to catalog file (defaults to default catalog path)

    Returns:
        open catalog context manager
    """
    with AliasCatalog(tool_name, catalog_path) as catalog:
        yield catalog
