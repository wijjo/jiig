"""Repetition specification and data class."""

from dataclasses import dataclass
from typing import Optional, Tuple, Union

from .log import log_error

# Raw repetition specification type.
RepeatSpec = Union[int, Tuple[Optional[int], Optional[int]]]


@dataclass
class Repetition:
    minimum: Optional[int]
    maximum: Optional[int]

    @classmethod
    def from_spec(cls, spec: Optional[RepeatSpec]) -> Optional['Repetition']:
        """
        Convert raw repeat specification to a Repeat object.

        Most of the code is purely sanity checking.

        :param spec: raw integer or pair of optional integers
        :return: Repeat object or None for bad or missing input data
        """
        if spec is None:
            return None
        if isinstance(spec, int):
            if spec > 0:
                return cls(spec, spec)
        elif isinstance(spec, tuple) and len(spec) == 2:
            if spec[0] is None:
                if spec[1] is None:
                    return cls(None, None)
                if isinstance(spec[1], int) and spec[1] >= 1:
                    return cls(spec[0], spec[1])
            elif isinstance(spec[0], int) and spec[0] >= 0:
                if spec[1] is None:
                    return cls(spec[0], None)
                if isinstance(spec[1], int) and spec[1] >= spec[0]:
                    return cls(spec[0], spec[1])
        log_error(f'Repeat specification {spec} is not one of the following:',
                  '- None for non-repeating field.',
                  '- A single integer for a specific required quantity.',
                  '- A tuple pair to express a range, with None meaning zero or infinity.')
        return None
