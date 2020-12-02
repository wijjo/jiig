"""
Jiig registry data.

Includes inspection types, dataclasses for registered tasks, arguments, etc.,
and a limited set of global (to this package) options.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Text, Any, Sequence, Tuple, Callable, Union, Type

from jiig.utility.footnotes import NoteDict, NotesList

ArgName = Text
Cardinality = Union[Text, int]
Description = Text

OptionFlag = Text
OptionFlagList = List[OptionFlag]
OptionFlagSpec = Union[OptionFlag, List[OptionFlag], Tuple[OptionFlag, OptionFlag]]

ArgumentAdapter = Callable[..., Any]


class RegisteredRunnerData:
    """Base class for data passed to runner constructors."""
    pass


class RegisteredRunner:
    """Base class for runners."""
    def __init__(self, data: RegisteredRunnerData):
        self.runner_data = data


TaskFunction = Callable[[RegisteredRunner], None]
TaskFunctionsSpec = List[TaskFunction]


@dataclass
class RegisteredTool:
    name: Optional[Text]
    description: Optional[Text]
    disable_alias: bool
    disable_help: bool
    disable_debug: bool
    disable_dry_run: bool
    disable_verbose: bool
    expose_hidden_tasks: bool
    notes: NotesList
    footnotes: NoteDict
    runner_cls: Optional[Type[RegisteredRunner]]


@dataclass
class Argument:
    name: ArgName
    adapters: List[ArgumentAdapter]
    description: Description = None
    cardinality: Cardinality = None
    flags: OptionFlagSpec = None
    default_value: Any = None
    choices: Sequence = None
    is_boolean: bool = False


@dataclass
class RegisteredTask:
    """
    Registered task that gets mapped into the command line interface.

    Created by the @task() decorator.
    """
    task_function: TaskFunction
    name: Text
    full_name: Text
    parent: Optional['RegisteredTask']
    description: Text
    notes: NotesList
    arguments: List[Argument]
    footnotes: Optional[NoteDict]
    execution_tasks: List['RegisteredTask']
    help_visibility: int
    # True on any task that accepts trailing arguments.
    receive_trailing_arguments: bool = False
    # Set to True when any child at any level has receive_trailing_arguments==True.
    capture_trailing_arguments: bool = False
    # Sub-tasks are added later when discovered child tasks reference as parent.
    sub_tasks: List['RegisteredTask'] = field(default_factory=list)


# Registered tool (only one).
REGISTERED_TOOL: Optional[RegisteredTool] = None

# All registered tasks.
REGISTERED_TASKS: List[RegisteredTask] = []

# All sorted registered tasks (cached).
REGISTERED_TASKS_SORTED: Optional[List[RegisteredTask]] = None

# Registered tasks indexed by function ID.
REGISTERED_TASKS_BY_ID: Dict[int, RegisteredTask] = {}

# Registered tasks indexed by name.
REGISTERED_TASKS_BY_NAME: Dict[Text, RegisteredTask] = {}
