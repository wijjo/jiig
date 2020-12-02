"""
Jiig tool argument declaration function.
"""

from typing import Any, Sequence

from jiig.registration import Argument, Description, ArgName, ArgumentAdapter, Cardinality

from .utility import _make_argument


def argument(name: ArgName,
             *adapters: ArgumentAdapter,
             description: Description = None,
             cardinality: Cardinality = None,
             default_value: Any = None,
             choices: Sequence = None,
             ) -> Argument:
    """
    Factory function for declaring an @task() or @sub_task() positional argument.

    :param name: argument destination name
    :param adapters: argument adapter chain for validation/conversion
    :param description: argument description
    :param cardinality: quantity specification based on argparse nargs
    :param default_value: default value for argument instance
    :param choices: restricted collection of value choices
    """
    return _make_argument(name,
                          *adapters,
                          description=description,
                          cardinality=cardinality,
                          default_value=default_value,
                          choices=choices)
