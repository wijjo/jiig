"""Data for a registered/mapped task argument."""


from dataclasses import dataclass
from typing import Type, Any, Sequence, List

from jiig.external.typing import ArgName, Description, Cardinality, OptionFlagSpec, \
    ArgumentTypeConversionFunction


@dataclass
class MappedArgument:
    name: ArgName
    type_cls: Type
    function: ArgumentTypeConversionFunction
    description: Description = None,
    cardinality: Cardinality = None,
    flags: OptionFlagSpec = None,
    positional: bool = False,
    default_value: Any = None,
    choices: Sequence = None


MappedArgumentList = List[MappedArgument]
