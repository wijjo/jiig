"""
Load tool runtime object.
"""

from jiig import model


def go(tool_config: model.Tool) -> model.ToolRuntime:
    """
    Prepare tool runtime object.

    :param tool_config: tool configuration data
    :return: tool runtime object
    """
    return model.ToolRuntime(tool_config)
