"""
Argument types for declarations.
"""

import inspect
from typing import Any, Union, Type, Sequence, Callable

from jiig.typing import ArgumentTypeConversionFunction, ArgumentTypeFactoryFunction, \
    ArgumentTypeFactoryOrConversionFunction, ArgName, OptionFlagSpec, \
    Cardinality, Description, Argument
from jiig.internal.registry import register_argument_type_factory, register_argument_type, \
    get_argument_type_factory, get_argument_type_conversion, \
    RegisteredArgumentTypeConversionFunction
from jiig.utility.general import make_list


def arg_type_factory(function: ArgumentTypeFactoryFunction = None):
    """
    @arg_type_factory decorator for registering argument type factory functions.

    May be used with or without call syntax.

    :param function: function received if the decorator is not called
    :return: function wrapper
    """
    def wrapper(decorated_function: ArgumentTypeFactoryFunction):
        register_argument_type_factory(decorated_function)
        return decorated_function
    if function:
        return wrapper(function)
    return wrapper


def arg_type(type_cls_or_function: Union[Callable, Type] = None):
    """
    @arg_type decorator for registering argument type conversion functions.

    May be used either with a type class argument or naked, i.e. without calling
    the decorator at all.

    :param type_cls_or_function: type class to determine argparse storage action
                                 (default: str)
    :return: function wrapper
    """
    def wrapper(function: ArgumentTypeConversionFunction):
        if type_cls_or_function is None or inspect.isfunction(type_cls_or_function):
            type_cls = None
        else:
            type_cls = type_cls_or_function
        signature = inspect.signature(function)
        if len(signature.parameters) != 1:
            raise TypeError(f'Argument type function "{function.__name__}" must'
                            f' have exactly one argument for a raw argument value.')
        name, parameter = list(signature.parameters.items())[0]
        # Grab default value from the signature.
        default_value = parameter.default if parameter.default != inspect.Parameter.empty else None
        register_argument_type(function, type_cls, default_value=default_value)
        return function
    if inspect.isfunction(type_cls_or_function):
        return wrapper(type_cls_or_function)
    return wrapper


def _get_registered_conversion(function: ArgumentTypeFactoryOrConversionFunction,
                               ) -> RegisteredArgumentTypeConversionFunction:
    registered_factory = get_argument_type_factory(function)
    if registered_factory:
        # Call a factory function to get an conversion function.
        try:
            # registered_type.function == function argument
            conversion_function = registered_factory.function()
        except Exception as exc:
            raise TypeError(f'Call to argument type function {function.__name__}'
                            f' failed with no arguments.', exc)
    else:
        conversion_function = function
    registered_conversion = get_argument_type_conversion(conversion_function)
    if not registered_conversion:
        raise TypeError(f'Argument type conversion function "{function.__name__}"'
                        f' was not registered using the @arg_type() decorator.')
    return registered_conversion


def argument(name: ArgName,
             argument_type_function: ArgumentTypeFactoryOrConversionFunction,
             description: Description = None,
             cardinality: Cardinality = None,
             flags: OptionFlagSpec = None,
             positional: bool = False,
             default_value: Any = None,
             choices: Sequence = None,
             ) -> Argument:
    """
    Factory function to create an argument for @task() or @sub_task().

    The `positional` boolean allows subclasses of Arg to pass along default
    flags, which get ignored when the argument is used positionally.

    :param name: argument destination name
    :param argument_type_function: argument type factory or conversion function
    :param description: argument description
    :param cardinality: quantity specification based on argparse nargs
    :param flags: option command line flags (if it's an option)
    :param positional: ignore flags, because this is a positional argument
    :param default_value: default value for argument instance
    :param choices: restricted collection of value choices
    """
    # Look up the registered conversion.
    conversion_function_data = _get_registered_conversion(argument_type_function)

    # Called for fatal error.
    def _type_error(*error_parts: Any):
        parts = [f'Argument "{name}" error']
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

    # Final default value, if any, is either passed in here or pulled from function signature.
    if default_value is not None:
        final_default_value = default_value
    else:
        final_default_value = conversion_function_data.default_value

    # Determine final flags list, if any, and validate.
    if positional:
        final_flags = None
    else:
        final_flags = make_list(flags)
        if any([not isinstance(f, str) or not f.startswith('-') for f in final_flags]):
            _type_error('bad flags', flags)

    return Argument(name,
                    conversion_function_data.type_cls,
                    conversion_function_data.function,
                    description=final_description,
                    cardinality=cardinality,
                    flags=final_flags,
                    positional=positional,
                    default_value=final_default_value,
                    choices=choices)
