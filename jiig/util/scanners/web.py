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
Awk-like web scraping with decorated classes.

*** This is a work in progress! ***

Uses efficient parsing that scans elements on the fly with the standard library
html.parser.HTMLParser class. It does not need to load an entire DOM tree in
memory before scanning begins.

Basic usage involves deriving a WScanner subclass and implementing @match()-
decorated methods that receive matches. The subclass can collect data as it
receives matches.

## @WScanner.match() decorator

Declares a method as a handler. Receives an element stack. The stack frame is
limited to the elements below the element where the state changed. States
automatically clear when the state start element end tag is reached.

    @WScanner.match(tag='h1', style_class='headline', text=r'^.*Breaking.*$', state='in_body')
    def handle_headline(stack: list[Element]):
        ...

### @match() keyword arguments

* tag: tag string
* style_class: required space-separated style class name(s)
* text: regular expression for matching element text
* state: state value where the matcher is active

Class name matching is not order-sensitive. Unmentioned additional classes in
the HTML `class` attribute are ignored.

The `text` keyword argument is a regular expression for matching all or portions
of the inner text block.

## Special methods:

### set_state(state)

Switch to a new state. Filters which handlers are used and which are ignored.
It can also change state via the set_state() method to efficiently route
processing to different matchers and handlers.

### end_scan()

Stop scanning and return.

https://docs.python.org/3.8/library/re.html#regular-expression-syntax

## To-Do

- Support regular expression options, like `re.IGNORECASE`.
- Support plain text scanning without regular expressions.
"""
import os
import re
from urllib.request import Request
from typing import Callable, Any, Optional, Hashable

from ..network import download_text


class NoStateCls:
    pass


NoState = NoStateCls()


class ElementScanner:

    def __init__(self,
                 tag: str,
                 style_classes: set[str],
                 text_pattern: re.Pattern,
                 function: Callable):
        self.tag = tag
        self.style_classes = style_classes
        self.text_pattern = text_pattern
        self.function = function


class WScanner:
    """Base class for awk-like web HTML scanners."""

    scanners: dict[Any, list[ElementScanner]] = None

    def __init__(self):
        self._state = None

    @classmethod
    def match(cls,
              tag: str = None,
              style_class: str = None,
              text: str = None,
              state: Any = None):
        """
        Decorator for methods that participate in HTML scanning and extraction.

        :param tag: case-insensitive tag literal for filtering elements
        :param style_class: style class regex patterns
        :param text: regular expression for searching the inner text block
        :param state: required state if set, or all states if not
        """
        if cls.scanners is None:
            cls.scanners = {}

        def _inner(function: Callable) -> Callable:
            element_scanner = ElementScanner(
                tag,
                set(style_class.split()),
                re.compile(text),
                function)
            cls.scanners.setdefault(state, []).append(element_scanner)
            return function

        return _inner

    def _call_line_handlers(self, line: str, state: Optional[Any]) -> bool:
        for matcher, handler in self.scanners.get(state, []):
            match = matcher.match(line)
            if match:
                handler(self, match)
        # TODO
        return False

    def scan(self,
             url_or_request: str | Request,
             headers: dict = None,
             timeout: float = None,
             state: Any = NoState,
             ):
        """
        Scan an HTML string, file, stream, or URL.

        :param url_or_request: HTML input URL or Request object
        :param headers: optional HTML headers
        :param timeout: timeout in seconds when downloading URL or Request
        :param state: next state value
        :return: self for chaining
        """
        text = download_text(url_or_request, headers=headers, timeout=timeout)
        if state is not NoState:
            self.set_state(state)
        self.begin()
        try:
            for line in text.split(os.linesep):
                for matcher, handler in self.scanners.get(self._state, []):
                    match = matcher.match(line)
                    if match:
                        handler(self, match)
        except StopIteration:
            pass
        # Make it chainable for one-liners.
        return self

    def end_scan(self):
        raise StopIteration

    def begin(self, *args, **kwargs):
        pass

    def get_state(self) -> Hashable:
        return self._state

    def set_state(self, state: Hashable):
        if state not in self.scanners:
            raise RuntimeError(f'State {state} is not supported by '
                               f'parser: {self.__class__.__name__}')
        self._state = state
