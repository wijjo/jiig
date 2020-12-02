"""
Jiig tool boolean option declaration function.
"""

from jiig.registration import ArgName, OptionFlagSpec, Description, Argument

from .utility import _make_argument


def bool_option(name: ArgName,
                flags: OptionFlagSpec,
                description: Description = None,
                ) -> Argument:
    """
    Factory function for declaring an @task() or @sub_task() boolean option.

    :param name: argument destination name
    :param flags: command line option flag(s)
    :param description: argument description
    """
    return _make_argument(name,
                          description=description,
                          flags=flags,
                          is_boolean=True)
