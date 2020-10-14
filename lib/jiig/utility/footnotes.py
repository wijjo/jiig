"""
Footnote-related utility functions and classes.

Footnotes are defined in dictionaries mapping labels to text blocks.

Footnote references are trailing square-bracketed labels.

E.g. "Blah blah blah [a][b]"

Labels may be any sequence of letters or numbers.
"""

import os
import re
from typing import Text, List, Optional, Iterator, Sequence, Dict

FootnoteDict = Dict[Text, Text]

# noinspection RegExpRedundantEscape
TRAILING_FOOTNOTE_REFERENCES_REGEX = re.compile(r'((?:\[\w*\]\s*)+)$')


class FootnoteBuilder:
    """Scrapes footnote labels from text blocks."""

    def __init__(self, *footnotes: FootnoteDict):
        self.labels: List[Text] = []
        self.context_labels: Dict[Text, List[Text]] = {}
        self.footnotes: FootnoteDict = {}
        self.add_footnotes(*footnotes)

    def add_footnotes(self, *footnotes: Optional[FootnoteDict]):
        for footnote_dictionary in footnotes:
            if footnote_dictionary:
                self.footnotes.update(footnote_dictionary)

    def scan_text(self,
                  text_block: Optional[Text],
                  context_labels: Sequence[Text] = None
                  ) -> Optional[Text]:
        """
        Scan text for "[label]" footnote markers.

        Keep track of the required footnotes.

        Replace "[label]" markers with numbered "[#]" markers.

        :param text_block: text block to scan and possibly modify
        :param context_labels: additional context labels for footnote(s)
        :return: possibly-modified text block
        """
        if text_block is None:
            return None
        markers_match = TRAILING_FOOTNOTE_REFERENCES_REGEX.search(text_block)
        if markers_match is None:
            return text_block
        parts = [text_block[:markers_match.start(1)].rstrip()]
        found_labels = markers_match.group(1).replace('[', '').replace(']', '').split()
        for label in found_labels:
            if label not in self.labels:
                self.labels.append(label)
                if context_labels:
                    self.context_labels.setdefault(label, []).extend(context_labels)
                parts.append(f'[{len(self.labels)}]')
        return ' '.join(parts)

    def format_footnotes(self) -> Iterator[Text]:
        for label_num, label in enumerate(self.labels, start=1):
            if label not in self.footnotes:
                yield f'(missing "{label}" footnote)'
            else:
                yield os.linesep.join([
                    ','.join([f'[{label_num}]'] + (self.context_labels.get(label) or [])),
                    self.footnotes[label].strip()
                ])
