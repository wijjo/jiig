"""
Jiig library.

<more library documentation goes here>
"""

# The `a` namespace provides convenient access to adapters.
from . import adapters as a
# The `f` namespace provides convenient access to field types.
from . import fields as f

# Other top level symbols.
from .field import Field
from .runtime import Runtime, RuntimeContext, HostContext
from .startup import main
from .task import Task
from .tool import Tool

from . import adapters, driver, fields, tasks, util
