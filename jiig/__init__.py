"""
Jiig library.

TODO: <more library documentation goes here>
"""

# Key types and functions exposed at the top level.
from .driver import Driver, DriverTask
from .field import Field
from .contexts import Context, ActionContext, Runtime, RuntimeHelpGenerator
from .runtime_task import RuntimeTask
from .runtime_tool import RuntimeTool
from .startup import main
from .task import Task
from .tool import Tool

# Top level public modules and their shortened aliases.
from . import adapters, fields, options
from . import adapters as a
from . import fields as f

# Top level public packages and their shortened aliases.
from . import contexts, driver, scripts, tasks, util
from . import contexts as c
from . import scripts as s
