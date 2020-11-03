"""Boolean argument type."""

from .argument_type import ArgumentType


class Boolean(ArgumentType):
    def __init__(self, default_value: bool = None):
        """
        Boolean constructor.

        :param default_value: default value when not provided
        """
        super().__init__(default_value=default_value)

    def argparse_prepare(self, params: dict):
        params['action'] = 'store_true'
