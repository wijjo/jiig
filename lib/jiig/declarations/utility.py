"""
Utility functions for declaration support.
"""

from inspect import isfunction, signature
from typing import Any, Sequence

from jiig.registration import ArgName, ArgumentAdapter, Description, Cardinality, \
    OptionFlagSpec, Argument
from jiig.utility.general import make_list


def _make_argument(name: ArgName,
                   *adapters: ArgumentAdapter,
                   description: Description = None,
                   cardinality: Cardinality = None,
                   flags: OptionFlagSpec = None,
                   default_value: Any = None,
                   choices: Sequence = None,
                   is_boolean: bool = False,
                   ) -> Argument:
    # Called for fatal error.
    def _type_error(*error_parts: Any):
        parts = [f'argument "{name}" error']
        if error_parts:
            parts.extend(map(str, error_parts))
        raise TypeError(': '.join(parts))

    # Check the name.
    if not isinstance(name, str) or not name:
        _type_error('invalid name')

    # Check and adjust the description.
    if description is not None and not isinstance(description, str):
        _type_error('bad description value', description)
    final_description = description or '(no argument description)'
    if default_value:
        final_description += f' (default: {default_value})'

    # Sanity check the cardinality.
    if cardinality is not None and (isinstance(cardinality, int) or
                                    cardinality not in ('*', '+', '?')):
        _type_error('bad cardinality value', cardinality)

    # Determine final flags list, if any, and validate.
    flag_list = make_list(flags)
    if any([not isinstance(f, str) or not f.startswith('-') for f in flag_list]):
        _type_error('bad flags', flags)

    # Sanity-check adapter function signatures.
    for adapter in adapters:
        if adapter not in (int, bool, float, str):
            if not isfunction(adapter):
                _type_error('non-function adapter', str(adapter))
            sig = signature(adapter)
            if not sig.parameters:
                _type_error('adapter function missing value parameter', adapter.__name__)
            elif len(sig.parameters) > 1:
                _type_error('adapter function has more than one parameter', adapter.__name__)

    return Argument(name,
                    list(adapters),
                    description=final_description,
                    cardinality=cardinality,
                    flags=flag_list,
                    default_value=default_value,
                    choices=choices,
                    is_boolean=is_boolean)
