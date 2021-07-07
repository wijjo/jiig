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

# Top level public modules and their shortened aliases.
from . import adapters, fields
from . import adapters as a
from . import fields as f

# Top level public packages and their shortened aliases.
from . import contexts, driver, scripts, tasks, util
from . import contexts as c
from . import scripts as s
