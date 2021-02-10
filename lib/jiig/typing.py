"""
Jiig type inspection types.
"""

from typing import Text, Any, Union, Callable

ArgumentAdapter = Callable[..., Any]
Cardinality = Union[Text, int]
OptionFlag = Text

RunFunction = Callable[['Runner', object], None]
DoneFunction = Callable[['Runner', object], None]
