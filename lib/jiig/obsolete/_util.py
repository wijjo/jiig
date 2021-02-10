"""
Utility functions and classes used during tool/task registration.
"""

import os
from dataclasses import dataclass
from typing import Text, Optional

from jiig.util.footnotes import NotesList


@dataclass
class RegisteredTextResults:
    """Prepared registered text."""
    description: Text
    notes: NotesList


def prepare_registered_text(description: Optional[Text],
                            notes: Optional[NotesList],
                            doc_string: Optional[Text],
                            ) -> RegisteredTextResults:
    """
    Provide final description and notes with fall-back defaults.

    Can pull fall-back text out of doc strings or hard-coded defaults.

    Guaranteed to return non-None data.

    :param description: source description
    :param notes: source notes
    :param doc_string: source doc string
    :return: description and notes wrapped in RegisteredTextResults object
    """
    if description is None or notes is None:
        if doc_string is None:
            doc_string = ''
        if description is None:
            doc_parts = doc_string.split(os.linesep, maxsplit=1)
            description = doc_parts[0].strip()
            if len(doc_parts) == 2:
                doc_string = doc_parts[1].strip()
            else:
                doc_string = ''
        if description is None:
            description = '(no description)'
        if notes is None:
            notes = []
            if doc_string:
                notes.append(doc_string)
    return RegisteredTextResults(description, notes)
