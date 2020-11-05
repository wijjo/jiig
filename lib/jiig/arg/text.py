"""String argument type."""

from jiig.external.argument import arg_type


@arg_type(str)
def text(value: str) -> str:
    """
    Text argument type function.

    :param value: string value
    :return: returned string value (same as input value)
    """
    return value
