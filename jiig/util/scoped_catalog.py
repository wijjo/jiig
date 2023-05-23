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

"""Persistent scoped data management.

Holds payload data with folder-based scoping.

Scope is a filesystem path or '' for global.

This module fully supports garbage-in/garbage-out. The caller is responsible for
generating and interpreting payload data types. The module also assumes payload
data compatible with JSON persistence.

TODO: Figure out a good way to use generics for better payload type checking.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Iterator,
    Self,
)
from .filesystem import create_folder
from .log import (
    log_error,
    log_message,
)
from .prompt import boolean_prompt
from .stream import read_json_file
from .text.table import format_table

# JSON schema:
# {
#   <name>: {
#     comment: <comment>,
#     payloads: {
#       <scope>: <payload>,
#       ...
#     },
#   },
#   ...
# }

GLOBAL_SCOPE_DISPLAY_NAME = '<global>'
MISSING_SCOPE_DISPLAY_NAME = '<missing>'
NAME_SCOPE_SEPARATOR = '@'


class Unspecified:
    """Mark unspecified function/method arguments,

    Can be used as default value when None is valid.
    """
    pass


@dataclass
class _ScopedItem:
    name: str
    global_payload: Any
    comment: str = None
    payload_map: dict[str, Any] = field(default_factory=dict)
    sorted: bool = False

    @property
    def sorted_payload_map(self) -> dict[str, Any]:
        if not self.sorted:
            self.payload_map = {
                name: self.payload_map[name]
                for name in sorted(self.payload_map.keys())
            }
            self.sorted = True
        return self.payload_map


class ScopedCatalogResult:
    """Result data returned by scoped catalog retrieval."""

    def __init__(self,
                 name: str,
                 scope: str = None,
                 item_exists: bool = False,
                 found_scope: str = None,
                 found_payload: Any = None,
                 ):
        """Scoped catalog result constructor.

        Args:
            name: parsed name
            scope: parsed scope or None if not specified
            item_exists: found item if True
            found_scope: found scope or None if not found
            found_payload: found payload or None if not found
        """
        self.name = name
        self.scope = scope
        self.item_exists = item_exists
        self.found_scope = found_scope
        self.found_payload = found_payload
        self.errors: list[str] = []


class ScopedCatalog:
    """Manages and provides access to scoped data catalog.

    It can be used as a context manager for a `with` block with automatic
    flushing of changes to a catalog file.

    In general, the consuming code should protect itself against exceptions.
    E.g. callers can call existence checking methods before invoking access
    methods that assume existence.
    """
    path: Path | None = None
    locked = False
    item_label = 'item'
    payload_label = 'payload'
    payload_label_plural = 'payloads'

    def __init__(self,
                 defaults: dict[str, Any] = None,
                 comments: dict[str, str] = None,
                 ):
        """ScopedCatalog constructor.

        Comments with names not in defaults are ignored.

        Args:
            defaults: optional initial name to default payload dictionary
            comments: optional initial comments by name
        """
        self._modified = False
        self._disable_saving = False
        self._item_map: dict[str, _ScopedItem] = {}
        # Defaults are not used elsewhere in this class, but scoped catalog
        # tasks may use the information to glean expected payload types.
        self.defaults = defaults or {}
        if defaults:
            for name, payload in defaults.items():
                comment = comments.get(name) if comments else None
                self._item_map[name] = _ScopedItem(name, payload, comment=comment)
        self._sorted = False
        self.load()

    def item_count(self) -> int:
        """Get item count.

        Returns:
            item count
        """
        return len(self._item_map)

    def exists(self, scoped_name: str) -> bool:
        """Check if item and payload (if "@scope" specified) exist.

        Args:
            scoped_name: item name (with or without "@scope")

        Returns:
            True if item/payload exists
        """
        name, scope = self.split_name(scoped_name)
        if scope is None or scope == '':
            return name in self._item_map
        return name in self._item_map and scope in self._item_map[name].payload_map

    def get(self, scoped_name: str) -> ScopedCatalogResult:
        """Get payload by name, with or without "@scope".

        If "@scope" is not specified, return result with payload of active scope
        based on current location.

        If "@scope" is specified, return result with payload if item and scoped
        payload exist.

        Args:
            scoped_name: item name (with or without "@scope")

        Returns:
            action result data
        """
        return self._get(scoped_name, False)

    def set(self,
            scoped_name: str,
            payload: Any,
            verbose: bool = False,
            ) -> ScopedCatalogResult:
        """Create or update catalog item payload.

        If "@scope" is not specified and item does not exist, create new one
        with global payload.

        If "@scope" is not specified and item exists, update payload assigned to
        active scope based on location.

        If "@scope" is specified, set payload for scope. Item must exist.

        Args:
            scoped_name: name[@scope] for receiving payload
            payload: payload to set
            verbose: display errors and messages if True

        Returns:
            action result data
        """
        result = self._get(scoped_name, verbose)
        if self.locked and result.found_scope is None:
            return result.error(
                'Not allowed to create new {item_label}: {name}',
            )
        if result.scope is not None and not result.item_exists:
            return result.error(
                'Must set global {payload_label} as default before setting'
                ' scoped one for: {name}',
            )
        # Already checked above that scope is None if item does not exist.
        if not result.item_exists:
            item = _ScopedItem(result.name, payload)
            result.found_scope = ''
            self._item_map[result.name] = item
            self._sorted = False
        else:
            item = self._item_map[result.name]
        if result.found_scope is not None:
            if result.found_scope == '':
                item.global_payload = payload
            else:
                item.payload_map[result.found_scope] = payload
        else:
            if result.scope is not None:
                result.found_scope = result.scope
            else:
                result.found_scope = self._get_active_scope(item)
            item.payload_map[result.found_scope] = payload
        item.sorted = False
        result.found_payload = payload
        self._modified = True
        result.message('Set {item_label}: {name}')
        return result

    def delete(self,
               scoped_name: str,
               verbose: bool = False,
               confirm: bool = False,
               ) -> ScopedCatalogResult:
        """Delete item/payload(s) by name.

        If "@scope" is not specified, delete payload for active scope or delete
        item if active scope is global ('').

        If "@scope" is specified, delete payload for scope. Item and scoped
        payload must exist. Scope must not be global.

        Args:
            scoped_name: name to delete, with or without "@scope"
            verbose: display errors and messages if True
            confirm: prompt for confirmation if True

        Returns:
            action result data
        """
        result = self._get(scoped_name, verbose)
        if self.locked and result.found_scope == '':
            result.found_scope = None
            result.found_payload = None
            return result.error(
                'Not allowed to delete {item_label}: {name}',
            )
        if not result.item_exists:
            return result.error(
                'Unable to delete missing {item_label}: {name}',
            )
        if result.scope == '':
            result.found_scope = None
            result.found_payload = None
            return result.error(
                'Not allowed to delete global {payload_label}: {name}',
            )
        if result.item_exists and result.found_payload is None:
            result.found_scope = None
            return result.error(
                'Unable to delete missing scoped {payload_label}:'
                ' {source_name}',
            )
        if confirm and not result.confirm('Delete {label} "{target_name}"'):
            result.found_scope = None
            result.found_payload = None
            return result.error(
                'Delete action abandoned: {source_name}'
            )
        item = self._item_map[result.name]
        if not result.found_scope:
            result.found_payload = item.global_payload
            del self._item_map[result.name]
        else:
            result.found_payload = item.payload_map[result.found_scope]
            del item.payload_map[result.found_scope]
        self._modified = True
        result.message('Deleted {label}: {target_name}')
        return result

    def rename(self,
               name1: str,
               name2: str,
               verbose: bool = False,
               ) -> ScopedCatalogResult:
        """Rename catalog item.

        Generate error (in result.errors) if catalog is locked, "@scope" is
        specified, source item is missing, or target item exists.

        Args:
            name1: name of item to rename
            name2: new item name
            verbose: display errors and messages if True

        Returns:
            action result data
        """
        source_result = self._get(name1, verbose)
        source_result.found_scope = None
        source_result.found_payload = None
        source_result.symbols['name2'] = name2
        target_result = self._get(name2, verbose)
        if self.locked:
            return source_result.error(
                'Not allowed to rename {item_label}: {name}',
            )
        if source_result.scope is not None or target_result.scope is not None:
            return source_result.error(
                'Rename {item_label} does not accept "@scope" specifiers.',
            )
        if not source_result.item_exists:
            return source_result.error(
                'Source {item_label} missing for rename: {name}',
            )
        if target_result.item_exists:
            return source_result.error(
                'Target {item_label} already exists for rename: {name2}',
            )
        self._item_map[name2] = self._item_map[name1]
        self._item_map[name2].name = name2
        del self._item_map[name1]
        self._sorted = False
        self._modified = True
        source_result.message('Renamed {item_label}: "{name}" -> "{name2}"')
        return source_result

    def comment(self,
                name: str,
                comment: str,
                verbose: bool = False,
                ) -> ScopedCatalogResult:
        """Set item comment.

        Generate error (in result.errors) if catalog is locked, "@scope" was
        specified for name, or item is missing.

        Args:
            name: name of item to receive comment
            comment: item comment, e.g. for help screen
            verbose: display errors and messages if True

        Returns:
            action result data
        """
        result = self._get(name, verbose)
        result.found_scope = None
        result.found_payload = None
        if self.locked:
            return result.error(
                'Not allowed to set {item_label} comment: {name}',
            )
        if result.scope is not None:
            return result.error(
                'Set {item_label} comment does not accept "@scope" specifier:'
                ' {source_name}',
            )
        if name not in self._item_map:
            return result.error(
                'Target {item_label} missing when setting comment: {name}',
            )
        self._item_map[name].comment = comment
        self._modified = True
        result.message('Set {item_label} comment succeeded: {name}')
        return result

    def query(self,
              name: str = None,
              scope: str | None = Unspecified,
              comment: str | None = Unspecified,
              payload: Any = Unspecified,
              active: bool = None,
              ) -> Iterator[tuple[str, str, str | None, Any, bool]]:
        """Query to generate item/payload tuples.

        If "@scope" is not specified yields all payloads.

        The active column is True when the scope is active.

        Args:
            name: optional name[@scope] for filtering
            scope: optional scope for filtering
            comment: optional comment value for filtering
            payload: optional payload value for filtering
            active: optional active boolean for filtering

        Yields:
            (name, scope, comment, payload, active) tuples
        """
        if name is not None:
            names = [name]
        else:
            names = list(self._sorted_item_map().keys())
        for scoped_name in names:
            query_name, query_scope = self.split_name(scoped_name)
            if query_name in self._item_map:
                item = self._item_map[query_name]
                if comment is not Unspecified and comment != item.comment:
                    continue
                current_scope = self._get_active_scope(item)

                def _row(row_scope: str) -> Iterator[tuple[str, str, str | None, Any, bool]]:
                    if row_scope == '':
                        row_payload = item.global_payload
                    else:
                        row_payload = item.payload_map[row_scope]
                    is_active = current_scope == row_scope
                    if ((scope is Unspecified or scope == row_scope)
                            and (payload is Unspecified or payload == row_payload)
                            and (active is None or active == is_active)):
                        yield item.name, row_scope, item.comment, row_payload, is_active

                yield from _row('')
                for check_scope in item.sorted_payload_map.keys():
                    yield from _row(check_scope)

    def query_strings(self,
                      name: str = None,
                      scope: str | None = Unspecified,
                      comment: str | None = Unspecified,
                      payload: Any = Unspecified,
                      active: bool = None,
                      ) -> Iterator[tuple[str, str, str, str]]:
        """Query to generate item/payload rows with stringized data.

        If "@scope" is not specified yields all payloads.

        Mark active scopes with "*" when not filtering on active state.

        Args:
            name: optional name[@scope] for filtering
            scope: optional scope for filtering
            comment: optional comment value for filtering
            payload: optional payload value for filtering
            active: optional active boolean for filtering

        Yields:
            (name, scope, comment, payload) tuples with string data
        """
        for qname, qscope, qcomment, qpayload, qactive in self.query(
            name=name,
            scope=scope,
            comment=comment,
            payload=payload,
            active=active,
        ):
            scope_string = qscope or GLOBAL_SCOPE_DISPLAY_NAME
            if active is None and qactive:
                scope_string += ' *'
            comment_string = qcomment or ''
            payload_string = self.payload_formatter(qpayload)
            yield qname, scope_string, comment_string, payload_string

    def format_table(self,
                     name: str = None,
                     scope: str | None = Unspecified,
                     comment: str | None = Unspecified,
                     payload: Any = Unspecified,
                     active: bool = None,
                     ) -> Iterator[str]:
        """Generate tabular catalog output.

        If "@scope" is not specified yields lines for all payloads.

        Args:
            name: optional name[@scope] for filtering
            scope: optional scope for filtering
            comment: optional comment value for filtering
            payload: optional payload value for filtering
            active: optional active boolean for filtering

        Yield:
            formatted table lines
        """
        headers = ['name', 'scope', 'comment', self.payload_label]
        for line in format_table(
            *self.query_strings(
                name=name,
                scope=scope,
                comment=comment,
                payload=payload,
                active=active,
            ),
            headers=headers,
        ):
            yield line

    def show(self,
             name: str = None,
             scope: str | None = Unspecified,
             comment: str | None = Unspecified,
             payload: Any = Unspecified,
             active: bool = None,
             ):
        """Show items and payloads.

        Args:
            name: optional name[@scope] for filtering
            scope: optional scope for filtering
            comment: optional comment value for filtering
            payload: optional payload value for filtering
            active: optional active boolean for filtering
        """
        have_active_scopes = False
        rows: list[tuple[str, str, str, str]] = []
        for name, scope, comment, payload in self.query_strings(
            name=name,
            scope=scope,
            comment=comment,
            payload=payload,
            active=active,
        ):
            rows.append((name, scope, comment, payload))
            if active is None and scope.endswith(' *'):
                have_active_scopes = True
        headers = ['name', 'scope', 'comment', self.payload_label]
        if rows:
            for line in format_table(*rows, headers=headers):
                log_message(line)
            if have_active_scopes:
                log_message('("*" marks active scopes)')
        else:
            if name is not None:
                log_message(f'{self.item_label.capitalize()} not found: {name}')
            else:
                log_message(f'No {self.payload_label_plural} to show.')

    def load(self):
        """Load catalog from file.

        Automatically called in constructor.
        """
        if self.path is None:
            return
        self._disable_saving = False
        errors: list[str] = []
        if self.path.exists():
            raw_catalog = read_json_file(self.path)
            if not isinstance(raw_catalog, dict):
                errors.append(f'Catalog data is not a JSON dictionary.')
            else:
                for name in sorted(raw_catalog.keys()):
                    item_data = raw_catalog[name]
                    if not isinstance(item_data, dict):
                        errors.append(f'Item "{name}" data is not a dictionary.')
                        continue
                    payloads = item_data.get('payloads')
                    if not payloads or not isinstance(payloads, dict) or '' not in payloads:
                        errors.append(f'Bad {self.payload_label} data: {name}')
                        continue
                    catalog_item = _ScopedItem(name, payloads[''])
                    comment = item_data.get('comment')
                    if not isinstance(payloads, dict):
                        errors.append(f'Item "{name}" payloads data is not a dictionary.')
                    if comment is not None:
                        catalog_item.comment = comment
                    if payloads:
                        for scope, payload in payloads.items():
                            if scope != '':
                                catalog_item.payload_map[scope] = payload
                                catalog_item.sorted = False
                    self._item_map[name] = catalog_item
        if errors:
            # Load errors are non-fatal to allow continuing in-memory-only.
            log_error(f'Failed to load: {self.path}', *errors)
            self._disable_saving = True
        self._modified = False

    def save(self):
        """Save catalog to file.

        Automatically called when class is used as context manager.
        """
        if self.path is None:
            return
        if self._disable_saving:
            log_error('Saving was disabled due to errors.',
                      'Please correct previous errors or delete the file.',
                      str(self.path))
            return
        create_folder(self.path.parent)
        try:
            with open(self.path, 'w', encoding='utf-8') as catalog_file:
                data: dict[str, dict[str, Any]] = {}
                for item in self._sorted_item_map().values():
                    data[item.name] = {}
                    if item.comment:
                        data[item.name]['comment'] = item.comment
                    data[item.name]['payloads'] = {'': item.global_payload}
                    for scope, payload in item.sorted_payload_map.items():
                        data[item.name]['payloads'][scope] = payload
                json.dump(data, catalog_file, indent=2)
                catalog_file.write(os.linesep)
            self._modified = False
        except Exception as exc:
            # Save errors are non-fatal to allow continuing in-memory-only.
            log_error(f'Failed to save: {self.path}', str(exc))

    def __enter__(self) -> Self:
        """Support construction in a `with` block."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Save on ending the `with` block if no exception occurred."""
        if exc_type is None and self._modified:
            self.save()
        return False

    @staticmethod
    def payload_formatter(payload: Any):
        """Default payload formatter - converts payload to string.

        Args:
            payload: payload to format

        Returns:
            payload string
        """
        return str(payload)

    @staticmethod
    def split_name(scoped_name: str) -> tuple[str, str | None]:
        """Split name[@scope].

        Args:
            scoped_name: name with optional "@scope"

        Returns:
            (name, scope) pair with scope=None when "@scope" wasn't specified
        """
        parts = scoped_name.split(NAME_SCOPE_SEPARATOR, maxsplit=1)
        if len(parts) == 1:
            return parts[0], None
        return parts[0], parts[1]

    @staticmethod
    def join_name(name: str, scope: str | None) -> str:
        """Join name and scope to form scoped name.

        Args:
            name: unscoped name
            scope: scope or None

        Returns:
            scoped name string
        """
        return name if scope is None else NAME_SCOPE_SEPARATOR.join([name, scope])

    @staticmethod
    def _get_active_scope(item: _ScopedItem) -> str:
        scope = os.getcwd()
        while True:
            if scope in item.payload_map:
                return scope
            next_scope = os.path.dirname(scope)
            if next_scope == scope:
                return ''
            scope = next_scope

    def _sorted_item_map(self) -> dict[str, _ScopedItem]:
        if not self._sorted:
            self._item_map = {
                key: self._item_map[key]
                for key in sorted(self._item_map.keys())
            }
            self._sorted = True
        return self._item_map

    class _Result(ScopedCatalogResult):
        def __init__(self,
                     name: str,
                     scope: str | None,
                     item_exists: bool,
                     found_scope: str | None,
                     found_payload: Any | None,
                     verbose: bool,
                     symbols: dict,
                     ):
            super().__init__(name=name,
                             scope=scope,
                             item_exists=item_exists,
                             found_scope=found_scope,
                             found_payload=found_payload)
            self.verbose = verbose
            self.symbols = symbols

        def _format_messages(self, *messages: str, **symbols) -> Iterator[str]:
            if symbols:
                format_symbols = self.symbols.copy()
                format_symbols.update(**symbols)
            else:
                format_symbols = self.symbols
            for message in messages:
                yield message.format(**format_symbols)
            return self

        def error(self, *messages: str, **symbols) -> Self:
            for formatted_message in self._format_messages(*messages, **symbols):
                self.errors.append(formatted_message)
                if self.verbose:
                    log_error(formatted_message)
            return self

        def message(self, *messages: str, **symbols):
            if self.verbose:
                for formatted_message in self._format_messages(*messages, **symbols):
                    log_message(formatted_message)

        def confirm(self, message: str, **symbols) -> bool:
            return boolean_prompt(next(self._format_messages(message, **symbols)))

    def _get(self, scoped_name: str, verbose: bool) -> _Result:
        name, scope = self.split_name(scoped_name)
        if scope:
            expanded_scope = os.path.abspath(scope)
        else:
            expanded_scope = scope
        if name not in self._item_map:
            item_exists = False
            found_scope = None
            payload = None
        else:
            item_exists = True
            item = self._item_map[name]
            if expanded_scope is not None:
                if expanded_scope in item.payload_map or expanded_scope == '':
                    found_scope = expanded_scope
                else:
                    found_scope = None
            else:
                found_scope = self._get_active_scope(item)
            if found_scope is not None:
                if found_scope == '':
                    payload = item.global_payload
                else:
                    payload = item.payload_map[found_scope]
            else:
                payload = None
        if expanded_scope is not None:
            source_name = self.join_name(name, scope)
        else:
            source_name = name
        target_name = self.join_name(name, found_scope)
        if found_scope is None:
            label = self.item_label
        else:
            label = self.payload_label
        scope_string = expanded_scope or GLOBAL_SCOPE_DISPLAY_NAME
        found_scope_string = found_scope or MISSING_SCOPE_DISPLAY_NAME
        return self._Result(
            name=name,
            scope=expanded_scope,
            item_exists=item_exists,
            found_scope=found_scope,
            found_payload=payload,
            verbose=verbose,
            symbols={
                'name': name,
                'scope': scope_string,
                'found_scope': found_scope_string,
                'source_name': source_name,
                'target_name': target_name,
                'item_label': self.item_label,
                'payload_label': self.payload_label,
                'label': label,
            },
        )
