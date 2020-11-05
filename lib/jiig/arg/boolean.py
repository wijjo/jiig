"""Boolean argument type."""

from jiig.external.argument import arg_type


@arg_type(bool)
def boolean(value: bool) -> bool:
    """
    Boolean argument type function.

    Argparse does the conversion, so this is a pass-through.

    :param value: boolean value
    :return: returned boolean value (same as input value)
    """
    return value
