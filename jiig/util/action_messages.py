"""
Action messages dataclass.
"""

from typing import Optional

from dataclasses import dataclass

from jiig.util.python import symbols_to_dataclass


@dataclass
class ActionMessages:
    before: str = None
    after: str = None
    success: str = None
    failure: str = None
    skip: str = None

    @classmethod
    def from_dict(cls, messages: Optional[dict]) -> 'ActionMessages':
        if messages is None:
            return cls()
        return symbols_to_dataclass(messages, cls)
