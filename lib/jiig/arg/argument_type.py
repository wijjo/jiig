"""Base Jiig argument type class."""

from typing import Optional, Any, Union, Type, Text, List, Sequence, Callable

ArgName = Text
Cardinality = Union[Text, int]
Description = Text
OptionFlag = Text
OptionFlagList = List[OptionFlag]


class ArgumentType:
    def __init__(self,
                 default_value: Any = None,
                 choices: Sequence = None):
        """
        ArgumentType constructor.

        The default_value here is only used when the argument value is missing
        and the Arg instance default_value is None.

        :param default_value: default value for argument type
        :param choices: acceptable values list
        """
        self.default_value = default_value
        self.choices = choices

    def argparse_prepare(self, params: dict):
        """
        Call-back to prepare argparse add_argument() keyword parameters.

        :param params: add_argument() keyword parameter dictionary to update
        """
        if self.default_value is not None:
            params['params'] = self.default_value
        if self.choices:
            params['choices'] = self.choices

    def process_data(self, data: Optional[Any]) -> Optional[Any]:
        """
        Call-back to validate and convert argument data.

        :param data: raw argument data
        :return: converted argument data
        :raises: ValueError: if data fails validation
        """
        return data


ArgumentTypeSpec = Union[ArgumentType, Type[ArgumentType]]


# === Functional interface

ArgumentTypeFunction = Callable[[Any], Any]
