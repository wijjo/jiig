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
Awk-like text processing with decorated classes.

Basic usage involves deriving a TScanner subclass and implementing
@handle()-decorated methods that receive matches. The subclass can collect data
as it receives matches.

It can also change state via the set_state() method to efficiently route
processing to different matchers and handlers.

The begin() method, if implemented is called at the start of a scan.

An @handle() method may call end_scan() to stop scanning and return. It can
also call next_line() to skip any other handlers for the current line.
"""

import re
from pathlib import Path
from typing import Callable, IO, Any, Iterator, cast

from ..stream import open_text_stream


class NextLine(Exception):
    """Exception used to move on to the next scanning line."""
    pass


class SubScannerBase:
    def __init__(self, function: Callable):
        self.function = function


class ScannerBase:
    """Base class for text, HTML, etc. scanners."""

    scanners: dict[Any, list[SubScannerBase]] = None

    def __init__(self, state: Any = None):
        self._state = state

    def scan(self,
             path_or_stream: str | Path | IO,
             ):
        """
        Scan a block of text from a string or stream.

        I/O exceptions may be raised.

        :param path_or_stream: input file path or stream
        """
        self.begin()
        with open_text_stream(path_or_stream) as text_stream:
            try:
                self.scan_text(text_stream)
            except StopIteration:
                pass
        # Make it chain-able for one-liners.
        return self

    def scan_text(self, text_stream):
        raise NotImplementedError

    def begin(self, *args, **kwargs):
        pass

    def end_scan(self):
        raise StopIteration

    def get_state(self) -> Any:
        return self._state

    def set_state(self, state: Any):
        if state not in self.scanners:
            raise RuntimeError(f'State {state} is not supported by '
                               f'parser: {self.__class__.__name__}')
        self._state = state

    def iterate_scanners(self) -> Iterator[SubScannerBase]:
        """Yield sub-scanners based on current state."""
        # If a non-None state has been set yield state-specific scanners.
        if self._state is not None:
            for scanner in self.scanners.get(self._state, []):
                yield scanner
        # Yield scanners mapped to None, which scan all states.
        for scanner in self.scanners.get(None, []):
            yield scanner

    @classmethod
    def register_scanner(cls, state: Any, sub_scanner: SubScannerBase):
        cls.scanners.setdefault(state, []).append(sub_scanner)


class TextLineScanner(SubScannerBase):
    def __init__(self,
                 text_pattern: str,
                 flags: int | re.RegexFlag,
                 function: Callable):
        self.pattern = re.compile(text_pattern, flags)
        super().__init__(function)


class TScanner(ScannerBase):
    """Base class for awk-like text scanners."""

    @classmethod
    def match(cls,
              pattern: str = None,
              flags: int | re.RegexFlag = 0,
              state: Any = None):
        if cls.scanners is None:
            cls.scanners = {}

        def _inner(function: Callable) -> Callable:
            cls.register_scanner(state, TextLineScanner(pattern, flags, function))
            return function

        return _inner

    def scan_text(self, text_stream):
        for line in text_stream.readlines():
            try:
                for line_scanner in self.iterate_scanners():
                    match = cast(TextLineScanner, line_scanner).pattern.match(line)
                    if match:
                        line_scanner.function(self, match)
            except NextLine:
                continue

    def next_line(self):
        raise NextLine()
