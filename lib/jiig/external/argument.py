"""
Argument types for declarations.
"""
from typing import List, Tuple, Union, Any

from jiig.arg.argument_type import ArgumentType, ArgumentTypeSpec, OptionFlag, \
    ArgName, Description, Cardinality
from jiig.utility.general import make_list


OptionFlagSpec = Union[OptionFlag, List[OptionFlag], Tuple[OptionFlag, OptionFlag]]


class Arg:
    """Wrapper for arguments declared in @task()/@sub_task()."""
    def __init__(self,
                 name: ArgName,
                 argument_type_spec: ArgumentTypeSpec,
                 description: Description = None,
                 cardinality: Cardinality = None,
                 flags: OptionFlagSpec = None,
                 positional: bool = False,
                 default_value: Any = None,
                 ):
        """
        Construct an argument for @task() or @sub_task().

        The `positional` boolean allows subclasses of Arg to pass along default
        flags, which get ignored when the argument is used positionally.

        :param name: argument destination name
        :param argument_type_spec: argument type class or instance
        :param description: argument description
        :param cardinality: quantity specification based on argparse nargs
        :param flags: option command line flags (if it's an option)
        :param positional: ignore flags, because this is a positional argument
        :param default_value: default value for argument instance
        """
        def _type_error(*error_parts: Any):
            parts = [f'Argument "{name}" error']
            if error_parts:
                parts.extend(map(str, error_parts))
            raise TypeError(': '.join(parts))
        if not isinstance(name, str) or not name:
            _type_error('invalid name')
        self.name = name
        if isinstance(argument_type_spec, ArgumentType):
            self.argument_type = argument_type_spec
        elif issubclass(argument_type_spec, ArgumentType):
            self.argument_type = argument_type_spec()
        else:
            _type_error('bad type specification', argument_type_spec)
        if description is not None and not isinstance(description, str):
            _type_error('bad description value', description)
        self.description = description or '(no argument description)'
        if default_value:
            self.description += f' (default: {default_value})'
        if cardinality is not None and (isinstance(cardinality, int) or
                                        cardinality not in ('*', '+', '?')):
            _type_error('bad cardinality value', cardinality)
        self.cardinality = cardinality
        self.flags = []
        if not positional:
            check_flags = make_list(flags)
            if all([isinstance(f, str) and f.startswith('-') for f in check_flags]):
                self.flags = check_flags
            else:
                _type_error('bad flags', flags)
        self.default_value = default_value


ArgList = List[Arg]
