"""Externally-visible inspection types."""

from typing import Callable, Any, Union, Text, List, Tuple

ArgName = Text
Cardinality = Union[Text, int]
Description = Text
OptionFlag = Text
OptionFlagList = List[OptionFlag]
OptionFlagSpec = Union[OptionFlag, List[OptionFlag], Tuple[OptionFlag, OptionFlag]]
ArgumentTypeConversionFunction = Callable[[Any], Any]
ArgumentTypeFactoryFunction = Callable[..., ArgumentTypeConversionFunction]
ArgumentTypeFactoryOrConversionFunction = Union[ArgumentTypeFactoryFunction,
                                                ArgumentTypeConversionFunction]
