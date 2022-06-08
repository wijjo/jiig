"""
Jiig library.

TODO: <more library documentation goes here>
"""

# Key types and functions exposed at the top level.
from .decorators import task
from .driver import Driver, DriverTask
from .contexts import Context, ActionContext
from .registry import AssignedTask, Field, ArgumentAdapter, \
    Runtime, RuntimeHelpGenerator, Tool, ToolOptions, JIIG_VENV_ROOT
from .startup import main
from .util.options import OPTIONS
from .util.script import Script

# Top level public modules and their shortened aliases.
from . import adapters as a
from . import fields as f
from . import contexts as c
from . import adapters, fields, contexts, driver, util, tasks
