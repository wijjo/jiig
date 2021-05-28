from dataclasses import dataclass


@dataclass
class Messages:
    heading: str = None
    success: str = None
    failure: str = None
    skip: str = None
