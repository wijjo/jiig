"""Registered hints"""

from typing import Text, List, Set


class _HintRegistry:

    supported_hints: Set[Text] = set()
    used_hints: Set[Text] = set()

    def add_supported_hints(self, *names: Text):
        """
        Register supported hint name(s).

        :param names: hint name(s)
        """
        for name in names:
            self.supported_hints.add(name)

    def add_used_hints(self, *names: Text):
        """
        Register used hint name(s).

        :param names: hint name(s)
        """
        for name in names:
            self.used_hints.add(name)

    def get_bad_hints(self) -> List[Text]:
        """
        Get hints that are used, but unsupported.

        :return: bad hints list
        """
        return list(sorted(self.used_hints.difference(self.supported_hints)))


HINT_REGISTRY = _HintRegistry()
