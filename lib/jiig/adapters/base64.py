"""
Jiig base64 encode/decode adapter functions.
"""

import base64
import binascii


def decode(value: str) -> str:
    """
    Decode base64 string.

    :param value: input base64 string
    :return: output utf-8 string
    """
    try:
        return base64.standard_b64decode(value).decode('utf-8')
    except binascii.Error as exc:
        # Wrap as ValueError, because binascii.Error will not be caught for the argument.
        raise ValueError(str(exc))


def encode(value: str) -> str:
    """
    Encode string to base64.

    :param value: input string
    :return: output base64 string
    """
    try:
        return base64.standard_b64encode(bytes(value, 'utf-8')).decode('utf-8')
    except binascii.Error as exc:
        # Wrap as ValueError, because binascii.Error will not be caught for the argument.
        raise ValueError(str(exc))
