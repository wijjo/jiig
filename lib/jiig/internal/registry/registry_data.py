"""Jiig registry data."""

from typing import Optional, List, Dict, Text, Set

from jiig.typing import RunnerFactoryFunction

from . import registry_types

# Runner factory registered by @runner_factory decorator. Last registered one wins.
RUNNER_FACTORY: Optional[RunnerFactoryFunction] = None

# All registered mapped tasks.
MAPPED_TASKS: List[registry_types.RegisteredTask] = []

# To help map task name in command line arguments to MappedTask by argparse destination names.
MAPPED_TASKS_BY_DEST_NAME: Dict[Text, registry_types.RegisteredTask] = {}

# For quick lookups of parent and dependency tasks while processing @task decorator calls.
MAPPED_TASKS_BY_ID: Dict[int, registry_types.RegisteredTask] = {}

# Names of tasks that are only shown when the ALL_TASKS option is used for help.
HIDDEN_TASK_NAMES: Set[Text] = set()

# Argument type factory functions.
ARGUMENT_TYPE_FACTORIES: Dict[int, registry_types.RegisteredArgumentTypeFactoryFunction] = {}

# Argument type conversion functions.
ARGUMENT_TYPE_CONVERSIONS: Dict[int, registry_types.RegisteredArgumentTypeConversionFunction] = {}
