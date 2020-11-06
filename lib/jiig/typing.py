"""Externally-visible inspection types."""

from dataclasses import dataclass
from typing import Callable, Any, Union, Text, List, Tuple, Dict, Type, Sequence

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

TaskFunction = Callable[['TaskRunner'], None]
TaskFunctionsSpec = List[TaskFunction]
RunnerFactoryFunction = Callable[['RunnerData'], 'TaskRunner']

NotesSpec = Union[Text, List[Text]]
NotesList = List[Text]
NoteDict = Dict[Text, Text]


@dataclass
class Argument:
    name: ArgName
    type_cls: Type
    function: ArgumentTypeConversionFunction
    description: Description = None,
    cardinality: Cardinality = None,
    flags: OptionFlagSpec = None,
    positional: bool = False,
    default_value: Any = None,
    choices: Sequence = None


ArgumentList = List[Argument]
