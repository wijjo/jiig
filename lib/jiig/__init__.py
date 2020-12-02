"""
One-stop-shopping for commonly-needed public symbols.
"""

# Public task runner data types.
from .task_runner import \
    RunnerData, \
    TaskRunner

# Public declaration functions and decorators.
from .declarations.argument_function import argument
from .declarations.bool_option_function import bool_option
from .declarations.option_function import option
from .declarations.sub_task_decorator import sub_task
from .declarations.task_decorator import task
from .declarations.tool_function import tool

# Public registry data types.
from .registration.data import \
    ArgName, \
    Argument, \
    ArgumentAdapter, \
    Cardinality, \
    Description, \
    OptionFlagSpec, \
    RegisteredTask, \
    RegisteredTool, \
    TaskFunction, \
    TaskFunctionsSpec

# Public packages.
from . import \
    adapters, \
    scanner, \
    tasks, \
    utility
