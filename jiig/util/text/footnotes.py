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

"""Footnote-related utility functions and classes.

Footnotes are defined in dictionaries mapping labels to text blocks.

Footnote references are written as "[^label]", which is the same as a common
Markdown extension for footnotes.

Parsed footnote declarations are paragraphs preceded by `[^label]: ` preambles.

Labels are sequences of valid symbol characters, like Python identifiers.

Example:

```
The rains in Spain [^spain] fall mainly on the plain [^plain].

[^spain]: Spain is a Western European country bordering the Atlantic ocean and
the Mediterranean Sea.

[^plain]: A plain is an area of flat terrain.
"""

import os
import re

NotesSpec = str | list[str]
NotesList = list[str]
NotesDict = dict[str, str]

FOOTNOTE_MARKER_REGEX = re.compile(r'\[\^(\w+)\]')
FOOTNOTE_DECLARATION_REGEX = re.compile(rf'^\s*\[\^(\w+)\]:\s*(.*)$', re.MULTILINE)


class FootnoteBuilder:
    """Scrapes footnote labels from text blocks."""

    def __init__(self):
        """FootnoteBuilder constructor."""
        self.labels: list[str] = []
        self.original_body_paragraphs: NotesList = []
        self.modified_body_paragraphs: NotesList = []
        self.footnotes: NotesDict = {}

    def add_footnotes(self, *footnotes: NotesDict | None):
        """
        Add footnotes that are available if referenced by markers.

        Args:
            footnotes: labeled footnote dictionary as keyword arguments
        """
        for footnote_dictionary in footnotes:
            if footnote_dictionary:
                self.footnotes.update(footnote_dictionary)

    def parse(self, text: str):
        """
        Parse text block(s) for footnote declarations.

        Capture non-footnote paragraphs in body_paragraphs.

        Args:
            text: text to parse
        """
        lines: list[str] = text.strip().split(os.linesep)
        paragraphs: NotesList = []
        is_new_paragraph = True
        for line in lines:
            line = line.strip()
            if line:
                if is_new_paragraph:
                    paragraphs.append(line)
                    is_new_paragraph = False
                else:
                    paragraphs[-1] = os.linesep.join([paragraphs[-1], line])
            else:
                is_new_paragraph = True
        for paragraph in paragraphs:
            tag_match = FOOTNOTE_DECLARATION_REGEX.match(paragraph)
            if tag_match:
                self.footnotes[tag_match.group(1)] = tag_match.group(2)
            else:
                self.original_body_paragraphs.append(paragraph)
                start_idx = 0
                parts: list[str] = []
                for matched in FOOTNOTE_MARKER_REGEX.finditer(paragraph):
                    if matched.start() > start_idx:
                        parts.append(paragraph[start_idx:matched.start()])
                        label_num = self._register_label(matched.group(1))
                        parts.append(f'[^{label_num}]')
                    start_idx = matched.end()
                if start_idx < len(paragraph):
                    parts.append(paragraph[start_idx:])
                self.modified_body_paragraphs.append(''.join(parts))

    def format_footnotes(self) -> NotesList:
        """
        Format footnotes reference text.

        :return: formatted text with footnote definitions
        """
        paragraphs: NotesList = []
        for label_num, label in enumerate(self.labels, start=1):
            if label not in self.footnotes:
                paragraphs.append(f'[^{label_num}]: "{label}" footnote not found.')
            else:
                paragraphs.append(f'[^{label_num}]: {self.footnotes[label].strip()}')
        return paragraphs

    def _register_label(self, label: str) -> int:
        for label_num, existing_label in enumerate(self.labels, start=1):
            if label == existing_label:
                return label_num
        self.labels.append(label)
        return len(self.labels)
