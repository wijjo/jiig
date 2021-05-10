"""
Persistent alias management.

See README.md for the design rationale.

At a high level, this module saves, loads, and manages aliases. Related to that,
it converts back and for between short and long alias names to support scoping.
"""

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Text, List, Optional, Iterator, Any, Iterable, Dict

from .console import abort, log_error, log_message, log_warning
from .process import shell_command_string
from .stream import read_json_source


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

DEFAULT_ALIASES_PATH = os.path.expanduser('~/.jiig-aliases')


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

    def _scrub_tool_data(self, tool_name: Text, tool_data: Any) -> Optional[Dict]:
        scrubbed_tool_data = {}
        if isinstance(tool_data, dict):
            for alias_name in sorted(tool_data.keys()):
                alias_data = self._scrub_alias_data(alias_name, tool_data[alias_name])
                if alias_data:
                    scrubbed_tool_data[alias_name] = alias_data
        else:
            self._error(f'Alias tool "{tool_name}" data is not a dictionary.')
        return scrubbed_tool_data or None

    def _scrub_alias_data(self, alias_name: Text, alias_data: Any) -> Optional[Dict]:
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

    def _error(self, message: Text):
        if not self.quiet:
            log_error(message)
        self.errors += 1


@dataclass
class Alias:
    """Returned alias data."""
    # The name is the long/fully-expanded name.
    name: Text
    description: Text
    command: List[Text]
    _short_name: Text = None

    @property
    def command_string(self) -> Text:
        return shell_command_string(*self.command)

    @property
    def short_name(self) -> Text:
        if self._short_name is None:
            self._short_name = shrink_alias_name(self.name)
        return self._short_name

    @property
    def label(self) -> Text:
        return os.path.basename(self.name)

    @property
    def path(self) -> Optional[Text]:
        return os.path.dirname(self.name) or None

    @property
    def short_path(self) -> Optional[Text]:
        return os.path.dirname(self.short_name) or None


def is_alias_name(name: Text) -> bool:
    """
    Check if name is an alias.

    :param name: name to check
    :return: True if it is an alias
    """
    return name[0] in (os.path.sep, '.', '~')


def expand_alias_name(short_name: Text, checked: bool = False) -> Optional[Text]:
    """
    Expand scoped alias name.

    Validation is not strict, and bad paths may be accepted.

    The current implementation is inefficient and has minimal validation.

    :param short_name: short alias name to expand
    :param checked: abort instead of raising exception
    :return: expanded name or None if it isn't a valid alias name
    :raise ValueError: if the alias name is bad
    """
    def _error(text: Text):
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


def shrink_alias_name(long_name: Text) -> Text:
    """
    Shrink paths using '.', '..', or '~', whenever possible.

    The current implementation is inefficient and has minimal validation.

    :param long_name: long alias name to shrink
    :return: shrunken name
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
    """
    Manages and provides access to a tool->alias->arguments map.

    It is not quiet. I.e. it validates read and write operations and displays
    errors as appropriate.

    It can be used as a context manager for a `with` block with automatic
    flushing of changes to an aliases file.
    """

    def __init__(self, tool_name: Text, catalog_path: Text):
        self.tool_name = tool_name
        self.catalog_path = catalog_path
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
        """
        Get all locations/aliases for current tool.

        :return: Alias object iterator
        """
        if not self.sorted:
            self._sort_catalog()
        return self._iterate_aliases()

    def get_alias(self, alias_name: Text) -> Optional[Alias]:
        """
        Get alias by name.

        Expand optional path that may precede the name.

        :param alias_name: alias name, possibly preceded by a path
        :return: alias data if found or None if not
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
        if os.path.exists(self.catalog_path):
            raw_catalog = read_json_source(file=self.catalog_path, check=True)
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
                     alias_name: Text,
                     command: Iterable[Text],
                     description: Text = None):
        """
        Create a new alias.

        :param alias_name: name of alias to create
        :param command: command arguments for alias (required)
        :param description: description of alias, e.g. for help screen
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
                     alias_name: Text,
                     command: Iterable[Text] = None,
                     description: Text = None):
        """
        Update an existing alias.

        :param alias_name: name of alias to update
        :param command: command arguments for alias (optional, or not updated)
        :param description: description of alias (optional, or not updated)
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

    def delete_alias(self, alias_name: Text):
        """
        Delete an alias by name after expanding any preceding path.

        :param alias_name: name of alias to delete
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

    def rename_alias(self, alias_name: Text, alias_name_new: Text):
        """
        Rename an alias.

        Applies to all locations for alias.

        :param alias_name: name of alias to rename
        :param alias_name_new: new target alias name
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

    def _iterate_aliases(self) -> Iterator[Alias]:
        """
        Get all locations/aliases for current tool.

        :return: Alias object iterator
        """
        tool_alias_map = self.catalog.get(self.tool_name)
        if tool_alias_map:
            for alias_name, alias_data in tool_alias_map.items():
                yield Alias(alias_name, alias_data['description'], alias_data['command'])

    def _sort_catalog(self):
        # Sort aliases by label, followed by path.
        sorted_catalog = {}
        for tool_name in sorted(self.catalog.keys()):
            sorted_aliases = sorted(self._iterate_aliases(),
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
def open_alias_catalog(tool_name: Text,
                       catalog_path: Text = None,
                       ) -> Iterator[AliasCatalog]:
    """
    Opens an alias catalog.

    It is not quiet. I.e. it validates read and write operations and displays
    errors as appropriate.

    It can be used as a context manager for a `with` block with automatic
    flushing of changes to an aliases file.

    :param tool_name: tool name for isolating applicable aliases from the catalog
    :param catalog_path: path to catalog file (defaults to default catalog path)
    :return: open catalog context manager
    """
    with AliasCatalog(tool_name, catalog_path or DEFAULT_ALIASES_PATH) as catalog:
        yield catalog
