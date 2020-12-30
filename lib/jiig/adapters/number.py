"""
Jiig numeric argument adapters.
"""

from typing import Optional

from jiig.registration.arguments import ArgumentAdapter


def make_int(value: str, base: int = 10) -> int:
    """
    Convert string to integer.

    :param value: input hex string
    :param base: conversion base (default: 10)
    :return: output integer value
    """
    return int(value, base=base)


def make_float(value: str) -> float:
    """
    Convert string to float.

    :param value: input hex string
    :return: output float value
    """
    return float(value)


def limit(minimum: Optional[float], maximum: Optional[float]) -> ArgumentAdapter:
    """
    Adapter factory for an input int/float number checked against limits.

    Type inspection for float also accepts an int type.

    This must be called to receive a parameterized function.

    :param minimum: minimum number value
    :param maximum: maximum number value
    :return: parameterized function to perform checking and conversion
    """
    def _number_range_inner(value: float) -> float:
        if not isinstance(value, (int, float)):
            raise TypeError('not int/float')
        if minimum is not None and value < minimum:
            raise ValueError(f'less than {minimum}')
        if maximum is not None and value > maximum:
            raise ValueError(f'more than {maximum}')
        return value
    return _number_range_inner
