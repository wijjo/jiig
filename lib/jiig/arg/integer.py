"""Integer argument type."""

from typing import Text, Optional

from jiig.external.argument import arg_type_factory, arg_type
from jiig.typing import ArgumentTypeConversionFunction


@arg_type_factory
def integer(minimum: Optional[int] = None,
            maximum: Optional[int] = None,
            ) -> ArgumentTypeConversionFunction:
    """
    Parameterized argument type function factory.

    Provides a parameterized closure for the argument type function that
    validates an integer value against limits.

    :param minimum: minimum value
    :param maximum: maximum value
    :return: parameterized closure function to perform checking and conversion
    """
    @arg_type(str)
    def integer_inner(value: Text) -> int:
        int_value = int(value)
        if minimum is not None and int_value < minimum:
            raise ValueError(f'Integer value {int_value} is less than the'
                             f' minimum, {minimum}.')
        if maximum is not None and int_value > maximum:
            raise ValueError(f'Integer value {int_value} is greater than the'
                             f' maximum, {maximum}.')
        return int_value
    return integer_inner
