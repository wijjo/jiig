"""Registered hints"""

from typing import Text, List, Optional, Set


class _Data:

    supported_hints: Set[Text] = set()
    used_hints: Set[Text] = set()
    _bad_hints: Optional[List[Text]] = None

    @classmethod
    def add_supported_hints(cls, *names: Text):
        """
        Register supported hint name(s).

        :param names: hint name(s)
        """
        for name in names:
            cls.supported_hints.add(name)
        cls._bad_hints = None

    @classmethod
    def add_used_hints(cls, *names: Text):
        """
        Register used hint name(s).

        :param names: hint name(s)
        """
        for name in names:
            cls.used_hints.add(name)
        cls._bad_hints = None

    @classmethod
    def get_bad_hints(cls) -> List[Text]:
        if cls._bad_hints is None:
            cls._bad_hints = list(sorted(cls.used_hints.difference(cls.supported_hints)))
        return cls._bad_hints


def add_supported_hints(*names: Text):
    """
    Register supported hint name(s).

    :param names: hint name(s)
    """
    _Data.add_supported_hints(*names)


def add_used_hints(*names: Text):
    """
    Register used hint name(s).

    :param names: hint name(s)
    """
    _Data.add_used_hints(*names)


def get_bad_hints() -> List[Text]:
    """
    Get (sorted) list of unsupported hint names used in field declarations.

    :return: sorted list of unsupported hint names
    """
    return _Data.get_bad_hints()
