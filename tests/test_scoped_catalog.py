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

"""Shell quoting test suite."""
import os
import re
import unittest
from typing import Any

from jiig.util.scoped_catalog import (
    NAME_SCOPE_SEPARATOR,
    ScopedCatalog,
    ScopedCatalogResult,
)


class TestScopedCatalog(unittest.TestCase):

    # noinspection PyPep8Naming
    def setUp(self) -> None:
        class TestCatalog(ScopedCatalog):
            path = None
            locked = False
            item_label = 'test item'
            payload_label = 'test payload'
            payload_label_plural = 'test payloads'
        self.catalog = TestCatalog()

    def check_result(self,
                     result: ScopedCatalogResult,
                     name: str,
                     scope: str | None,
                     found_scope: str | None,
                     found_payload: Any | None,
                     errors: list[str] = None,
                     ):
        if scope:
            scope = os.path.abspath(scope)
        if found_scope:
            found_scope = os.path.abspath(found_scope)
        self.assertEqual(result.name, name, 'Name mismatch')
        self.assertEqual(result.scope, scope, 'Scope mismatch')
        self.assertEqual(result.found_scope, found_scope, 'Found scope mismatch')
        self.assertEqual(result.found_payload, found_payload, 'Payload mismatch')
        errors = errors or []
        self.assertEqual(len(result.errors), len(errors), 'Error count mismatch')
        for idx, error_pattern in enumerate(errors):
            text = result.errors[idx]
            regex = re.compile(fr'^.*{error_pattern}.*$', re.IGNORECASE)
            self.assertRegexpMatches(text, regex, 'Error pattern mismatch')

    def check_get(self, name: str, scope: str | None, payload: Any | None):
        parts = name.split(NAME_SCOPE_SEPARATOR)
        self.check_result(
            self.catalog.get(name),
            parts[0],
            parts[1] if len(parts) == 2 else None,
            scope,
            payload,
        )

    def check_set(self, name: str, payload: Any, scope: str | None):
        parts = name.split(NAME_SCOPE_SEPARATOR)
        self.check_result(
            self.catalog.set(name, payload),
            parts[0],
            parts[1] if len(parts) == 2 else None,
            scope,
            payload,
        )

    def check_set_error(self, name: str, payload: Any, error: str):
        parts = name.split(NAME_SCOPE_SEPARATOR)
        self.check_result(
            self.catalog.set(name, payload),
            parts[0],
            parts[1] if len(parts) == 2 else None,
            None,
            None,
            errors=[error],
        )

    def check_delete(self, name: str, scope: str | None, payload: Any | None):
        parts = name.split(NAME_SCOPE_SEPARATOR)
        self.check_result(
            self.catalog.delete(name),
            parts[0],
            parts[1] if len(parts) == 2 else None,
            scope,
            payload,
        )

    def check_delete_error(self, name: str, error: str):
        parts = name.split(NAME_SCOPE_SEPARATOR)
        self.check_result(
            self.catalog.delete(name),
            parts[0],
            parts[1] if len(parts) == 2 else None,
            None,
            None,
            errors=[error],
        )

    def check_rename(self, name1: str, name2: str):
        parts1 = name1.split(NAME_SCOPE_SEPARATOR)
        self.check_result(
            self.catalog.rename(name1, name2),
            parts1[0],
            parts1[1] if len(parts1) == 2 else None,
            None,
            None,
        )

    def check_rename_error(self, name1: str, name2: str, error: str):
        parts1 = name1.split(NAME_SCOPE_SEPARATOR)
        self.check_result(
            self.catalog.rename(name1, name2),
            parts1[0],
            parts1[1] if len(parts1) == 2 else None,
            None,
            None,
            errors=[error],
        )

    def check_comment(self, name: str, comment: str):
        parts = name.split(NAME_SCOPE_SEPARATOR)
        self.check_result(
            self.catalog.comment(name, comment),
            parts[0],
            parts[1] if len(parts) == 2 else None,
            None,
            None,
        )

    def check_comment_error(self, name: str, comment: str, error: str):
        parts = name.split(NAME_SCOPE_SEPARATOR)
        self.check_result(
            self.catalog.comment(name, comment),
            parts[0],
            parts[1] if len(parts) == 2 else None,
            None,
            None,
            errors=[error],
        )

    def check_data(self, *rows: tuple[str, str, str | None, Any, bool]):
        actual_rows = list(self.catalog.query())
        expected_rows = [
            (name, os.path.abspath(scope) if scope else scope, comment, payload, is_current)
            for name, scope, comment, payload, is_current in sorted(rows)
        ]
        self.assertListEqual(actual_rows, expected_rows, 'Catalog data mismatch')

    def test_set_get_simple(self):
        self.check_set('aaa', 'abc', '')
        self.check_get('aaa', '', 'abc'),
        self.check_data(('aaa', '', None, 'abc', True))

    def test_set_scope_to_missing_item(self):
        self.check_set_error('aaa@', 'abc', 'Must set global test payload as default')
        self.check_data()

    def test_set_scoped_payload(self):
        self.check_set('aaa', 'abc', '')
        self.check_set('aaa@.', 'def', '.')
        self.check_data(('aaa', '', None, 'abc', False),
                        ('aaa', '.', None, 'def', True))

    def test_set_with_multiple_scopes(self):
        self.check_set('aaa', 'abc', '')
        self.check_set('aaa@/etc', 'def', '/etc')
        parent = os.path.dirname(os.getcwd())
        self.check_set(f'aaa@{parent}', 'ghi', parent)
        self.check_set('aaa', 'jkl', parent)
        self.check_data(('aaa', '', None, 'abc', False),
                        ('aaa', '/etc', None, 'def', False),
                        ('aaa', parent, None, 'jkl', True))

    def test_set_locked_create(self):
        self.catalog.locked = True
        self.check_set_error('aaa', 'abc', 'Not allowed to create new test item')
        self.check_set_error('aaa@scope', 'abc', 'Not allowed to create new test item')
        self.check_data()

    def test_delete_locked(self):
        self.check_set('aaa', 'abc', '')
        self.catalog.locked = True
        self.check_delete_error('aaa', 'Not allowed to delete test item')
        self.check_data(('aaa', '', None, 'abc', True))

    def test_delete_from_empty_catalog(self):
        self.check_delete_error('aaa', 'Unable to delete missing test item')
        self.check_data()

    def test_delete_missing_item(self):
        self.check_set('aaa', 'abc', '')
        self.check_delete_error('bbb', 'Unable to delete missing test item')
        self.check_data(('aaa', '', None, 'abc', True))

    def test_delete_missing_payload(self):
        self.check_set('aaa', 'abc', '')
        self.check_delete_error('aaa@here', 'delete missing scoped test payload')
        self.check_data(('aaa', '', None, 'abc', True))

    def test_delete_global_payload_error(self):
        self.check_set('aaa', 'abc', '')
        self.check_delete_error('aaa@', 'Not allowed to delete global test payload')
        self.check_data(('aaa', '', None, 'abc', True))

    def test_delete_item(self):
        self.check_set('aaa', 'abc', '')
        self.check_delete('aaa', '', 'abc')
        self.check_data()

    def test_delete_item_with_payloads(self):
        self.check_set('aaa', 'abc', '')
        self.check_set('aaa@scope1', 'def', 'scope1')
        self.check_set('aaa@scope2', 'ghi', 'scope2')
        self.check_delete('aaa', '', 'abc')
        self.check_data()

    def test_delete_payload(self):
        self.check_set('aaa', 'abc', '')
        self.check_set('aaa@..', 'def', '..')
        self.check_set('aaa@.', 'ghi', '.')
        self.check_delete('aaa@..', '..', 'def')
        self.check_data(('aaa', '', None, 'abc', False),
                        ('aaa', '.', None, 'ghi', True))

    def test_delete_closest_payload(self):
        self.check_set('aaa', 'abc', '')
        self.check_set('aaa@..', 'ghi', '..')
        self.check_set('aaa@.', 'def', '.')
        self.check_delete('aaa', '.', 'def')
        self.check_data(('aaa', '', None, 'abc', False),
                        ('aaa', '..', None, 'ghi', True))

    def test_rename(self):
        self.check_set('aaa', 'abc', '')
        self.check_rename('aaa', 'bbb')
        self.check_data(('bbb', '', None, 'abc', True))

    def test_rename_locked(self):
        self.check_set('aaa', 'abc', '')
        self.catalog.locked = True
        self.check_rename_error('aaa', 'bbb', 'Not allowed to rename test item')
        self.check_data(('aaa', '', None, 'abc', True))

    def test_rename_with_scope_error(self):
        self.check_set('aaa', 'abc', '')
        self.check_rename_error('aaa@x', 'bbb', 'not accept "@scope" specifiers')
        self.check_rename_error('aaa', 'bbb@y', 'not accept "@scope" specifiers')
        self.check_data(('aaa', '', None, 'abc', True))

    def test_rename_source_missing(self):
        self.check_rename_error('aaa', 'bbb', 'missing for rename')

    def test_rename_target_exists(self):
        self.check_set('aaa', 'abc', '')
        self.check_set('bbb', 'def', '')
        self.check_rename_error('aaa', 'bbb', 'already exists for rename')
        self.check_data(('aaa', '', None, 'abc', True),
                        ('bbb', '', None, 'def', True))

    def test_set_comment(self):
        self.check_set('aaa', 'abc', '')
        self.check_comment('aaa', 'a comment')
        self.check_data(('aaa', '', 'a comment', 'abc', True))

    def test_set_comment_multiple_scopes(self):
        self.check_set('aaa', 'abc', '')
        self.check_set('aaa@.', 'def', '.')
        self.check_comment('aaa', 'a comment')
        self.check_data(('aaa', '', 'a comment', 'abc', False),
                        ('aaa', '.', 'a comment', 'def', True))

    def test_set_comment_locked(self):
        self.check_set('aaa', 'abc', '')
        self.catalog.locked = True
        self.check_comment_error('aaa', 'a comment', 'Not allowed to set test item comment')
        self.check_data(('aaa', '', None, 'abc', True))

    def test_set_comment_errors(self):
        self.check_set('aaa', 'abc', '')
        self.check_comment_error('aaa@scope', 'a comment', 'does not accept "@scope"')
        self.check_comment_error('bbb', 'a comment', 'missing when setting comment')
        self.check_comment('aaa', 'a comment')
        self.check_data(('aaa', '', 'a comment', 'abc', True))
