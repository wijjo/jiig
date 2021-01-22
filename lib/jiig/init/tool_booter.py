"""
Boot tool given previously-loaded bootstrap data.
"""

from inspect import isclass

from jiig import model
from jiig.util.console import abort


def initialize(bootstrap: model.ToolBootstrap) -> model.RegisteredTool:
    """
    Load the tool script and provide the registered tool.

    :param bootstrap: tool bootstrap object
    """
    # Call bootstrap function to get a Tool class.
    tool_class = bootstrap.on_boot()
    if not isclass(tool_class) or not issubclass(tool_class, model.Tool):
        abort('Tool bootstrap function must return a Tool class type.')
    return model.RegisteredTool(bootstrap, tool_class)
