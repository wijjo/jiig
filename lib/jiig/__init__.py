"""
One-stop-shopping for commonly-needed public symbols.
"""

# Public task runner data types.
from .task_runner import \
    RunnerData, \
    TaskRunner

# Public declaration functions, including argument and option functions, plus
# tool, task, and runner factory decorators.
from .declarations import \
    argument, \
    bool_option, \
    option, \
    runner_factory, \
    sub_task, \
    task, \
    tool

# Public registry data types.
from .registry.data import \
    ArgName, \
    Argument, \
    ArgumentAdapter, \
    Cardinality, \
    Description, \
    OptionFlagSpec, \
    RegisteredTask, \
    RegisteredTool, \
    RunnerFactoryFunction, \
    TaskFunction, \
    TaskFunctionsSpec

# Public packages.
from . import \
    adapters, \
    scanner, \
    tasks, \
    utility
