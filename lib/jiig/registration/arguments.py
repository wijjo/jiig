"""
Registered task argument dataclass.
"""

from inspect import isfunction, signature
from typing import Text, List, Any, Sequence, Tuple, Union, Callable

from jiig.utility.general import make_list

ArgumentAdapter = Callable[..., Any]
Cardinality = Union[Text, int]
OptionFlag = Text
OptionFlagList = List[OptionFlag]
OptionFlagSpec = Union[OptionFlag, List[OptionFlag], Tuple[OptionFlag, OptionFlag]]


class Arg:
    """
    Generic argument class for all argument types.

    Can be used directly for simple pass-through text arguments, or can serve as
    a base class for other argument and option types.
    """
    def __init__(self,
                 name: Text,
                 description: Text,
                 *adapters: ArgumentAdapter,
                 cardinality: Cardinality = None,
                 default_value: Any = None,
                 choices: Sequence = None,
                 ):
        """
        Generic argument constructor.

        :param name: argument name used for data attribute
        :param description: description
        :param adapters: optional data type adapters
        :param cardinality: optional cardinality as count, '*', '+', or '?'
        :param default_value: optional default value
        :param choices: optional restricted value set as sequence
        """
        # Called for fatal error.
        def _type_error(*error_parts: Any):
            parts = [f'argument "{name}" error']
            if error_parts:
                parts.extend(map(str, error_parts))
            raise TypeError(': '.join(parts))

        # Check the name.
        if not isinstance(name, str) or not name:
            _type_error('invalid name')
        self.name = name

        # Sanity-check adapter function signatures.
        if adapters:
            for adapter in adapters:
                if adapter not in (int, bool, float, str):
                    if not isfunction(adapter):
                        _type_error('non-function adapter', str(adapter))
                    sig = signature(adapter)
                    if not sig.parameters:
                        _type_error('adapter function missing value parameter', adapter.__name__)
                    elif len(sig.parameters) > 1:
                        _type_error('adapter function has more than one parameter', adapter.__name__)
        self.adapters = make_list(adapters)

        # Check and adjust the description.
        if description is not None and not isinstance(description, str):
            _type_error('bad description value', description)
        self.description = description or '(no argument description)'
        if default_value:
            self.description += f' (default: {default_value})'

        # Sanity check the cardinality.
        if cardinality is not None and (isinstance(cardinality, int) or
                                        cardinality not in ('*', '+', '?')):
            _type_error('bad cardinality value', cardinality)
        self.cardinality = cardinality

        self.default_value = default_value
        self.choices = choices

    @property
    def multi_value(self) -> bool:
        """
        Determine if argument cardinality results in value being a list.

        :return: True if argument value is a list.
        """
        if self.cardinality is not None:
            if isinstance(self.cardinality, int):
                return self.cardinality > 1
            return self.cardinality in ('*', '+')
        return False


class Opt(Arg):
    def __init__(self,
                 flags: OptionFlagSpec,
                 name: Text,
                 description: Text,
                 *adapters: ArgumentAdapter,
                 cardinality: Cardinality = None,
                 default_value: Any = None,
                 choices: Sequence = None,
                 # Use BoolOpt instead of adding this private keyword.
                 _is_boolean: bool = False,
                 ):
        """
        Generic option constructor.

        :param flags: option flag string or string sequence
        :param name: argument name used for data attribute
        :param description: optional description
        :param adapters: optional data type adapters
        :param cardinality: optional cardinality as count, '*', '+', or '?'
        :param default_value: optional default value
        :param choices: optional restricted value set as sequence
        """
        # Determine final flags list, if any, and validate.
        self.flags = make_list(flags)
        if any([not isinstance(f, str) or not f.startswith('-') for f in self.flags]):
            raise TypeError(f'Bad option flag specification.', flags)
        self.is_boolean = _is_boolean
        super().__init__(name,
                         description,
                         *adapters,
                         cardinality=cardinality,
                         default_value=default_value,
                         choices=choices)


class BoolOpt(Opt):
    def __init__(self,
                 flags: OptionFlagSpec,
                 name: Text,
                 description: Text,
                 ):
        """
        Generic option constructor.

        :param flags: option flag string or string sequence
        :param name: argument name used for data attribute
        :param description: optional description
        """
        super().__init__(flags, name, description, _is_boolean=True)
