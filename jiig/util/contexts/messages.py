"""
Action messages dataclass.
"""

from typing import Optional

from dataclasses import dataclass

from ..python import symbols_to_dataclass


@dataclass
class Messages:
    before: str = None
    after: str = None
    success: str = None
    failure: str = None
    skip: str = None

    @classmethod
    def from_dict(cls, messages: Optional[dict]) -> 'Messages':
        if messages is None:
            return cls()
        return symbols_to_dataclass(messages, cls)
