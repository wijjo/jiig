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

import unittest

from jiig.util.process import simple_shell_quote


class TestShellQuoting(unittest.TestCase):

    @staticmethod
    def check(raw_value: str,
              expected_argument_string: str,
              expected_literal_string: str,
              ):
        argument_string = simple_shell_quote(raw_value)
        literal_string = simple_shell_quote(raw_value, literal=True)
        errors: list[str] = []
        if argument_string != expected_argument_string:
            errors.append(f'{argument_string} != {expected_argument_string}')
        if literal_string != expected_literal_string:
            errors.append(f'{literal_string} != {expected_literal_string}')
        if errors:
            raise AssertionError(f'Quoting failed: {" and ".join(errors)}')

    def test_simple(self):
        self.check('abc', 'abc', 'abc')

    def test_middle_space(self):
        self.check('ab c', '"ab c"', "'ab c'")

    def test_pre_quoted(self):
        self.check('"abc"', r'"\"abc\""', """'"abc"'""")

    def test_pre_quoted_with_trailing_space(self):
        self.check('"abc" ', r'"\"abc\" "', """'"abc" '""")

    def test_escaped_character(self):
        self.check(r'xy\z', r'"xy\z"', r"'xy\z'")
