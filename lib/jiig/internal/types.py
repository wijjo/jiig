"""Base and inspection types."""

from typing import List, Text, Callable, Dict, Union, Sequence, Tuple

OptionRawFlags = Union[Text, Sequence[Text]]
OptionRawDict = Dict[OptionRawFlags, Dict]
OptionFlags = Tuple[Text]
OptionDict = Dict[OptionFlags, Dict]
OptionDestFlagsDict = Dict[Text, OptionFlags]
ArgumentList = List[Dict]

TaskFunction = Callable[['TaskRunner'], None]
RunnerFactoryFunction = Callable[['RunnerData'], 'TaskRunner']
