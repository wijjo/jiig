"""
Jiig boolean adapters.
"""


def make_bool(value: str) -> bool:
    """
    Convert yes/no/true/false string to bool.

    :param value: input boolean string
    :return: output boolean value
    """
    if not isinstance(value, str):
        raise TypeError(f'not a string')
    lowercase_value = value.lower()
    if lowercase_value in ('yes', 'true'):
        return True
    if lowercase_value in ('no', 'false'):
        return False
    raise ValueError(f'bad boolean string')
