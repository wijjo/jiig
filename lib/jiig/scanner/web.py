# Copyright 2020 Steven Cooper
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    def handle_headline(stack: List[Element]):
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

import re
from urllib.request import Request
from typing import List, Callable, Text, IO, Dict, Any, Set, Optional, Hashable
from jiig.utility.stream import open_text


class NoStateCls:
    pass


NoState = NoStateCls()


class ElementScanner:

    def __init__(self,
                 tag: Text,
                 style_classes: Set[Text],
                 text_pattern: re.Pattern,
                 function: Callable):
        self.tag = tag
        self.style_classes = style_classes
        self.text_pattern = text_pattern
        self.function = function


class WScanner:
    """Base class for awk-like web HTML scanners."""

    scanners: Dict[Any, List[ElementScanner]] = None

    def __init__(self):
        self._state = None

    @classmethod
    def match(cls,
              tag: Text = None,
              style_class: Text = None,
              text: Text = None,
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

    def _call_line_handlers(self, line: Text, state: Optional[Any]) -> bool:
        for matcher, handler in self.scanners.get(state, []):
            match = matcher.match(line)
            if match:
                handler(self, match)
        # TODO
        return False

    def scan(self,
             *,
             text: Text = None,
             file: Text = None,
             stream: IO = None,
             url: Text = None,
             request: Request = None,
             timeout: int = None,
             state: Any = NoState):
        """
        Scan an HTML string, file, stream, or URL.

        :param text: HTML input string
        :param file: HTML file path
        :param stream: HTML input stream
        :param url: HTML input URL for downloading HTML
        :param request: HTML input Request object for downloading HTML
        :param timeout: timeout in seconds when downloading URL or Request
        :param state: next state value
        """
        with open_text(text=text,
                       file=file,
                       stream=stream,
                       url=url,
                       request=request,
                       timeout=timeout,
                       check=True) as html_stream:
            if state is not NoState:
                self.set_state(state)
            self.begin()
            try:
                for line in html_stream.readlines():
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
