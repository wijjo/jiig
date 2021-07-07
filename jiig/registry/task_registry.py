"""
Task registry.

Uses common Registry support, but adds data to the registration record and
provides a more type-specific API for accessing and querying the registry.
"""

import re
import sys
from dataclasses import dataclass
from inspect import isfunction, ismodule
from typing import Text, Dict, List, Optional, Union, cast, Any, Callable, Sequence
from types import ModuleType

from ..util.general import DefaultValue, plural
from ..util.log import log_warning, log_error, abort
from ..util.footnotes import NotesList, NotesDict, FootnoteBuilder
from ..util.python import get_function_fields
from ..util.repetition import Repetition

from .context_registry import SelfRegisteringContextBase
from ._registry import RegistrationRecord, Registry
from .field import Field, ArgumentAdapter

DEFAULT_TASK_DESCRIPTION = '(no description, e.g. in task doc string)'
TASK_IDENT_REGEX = re.compile(r'^'
                              r'([a-zA-Z][a-zA-Z0-9\-_]*)'
                              r'(?:\[(s|secondary|h|hidden)\])?'
                              r'$')

# The best we can do for now for a task function type hint, because Callable has
# no syntax for variable keyword arguments.
TaskFunction = Callable
TaskReference = Union[Text, ModuleType, TaskFunction]
SubTaskList = Sequence[TaskReference]
SubTaskDict = Dict[Text, TaskReference]
SubTaskCollection = Union[SubTaskList, SubTaskDict]
TaskImplementation = TaskFunction


@dataclass
class TaskField:
    """Data extracted from task dataclass or task function signature."""
    name: Text
    description: Text
    element_type: Any
    field_type: Any
    default: Optional[DefaultValue]
    repeat: Optional[Repetition]
    choices: Optional[List]
    hints: Dict
    adapters: List[ArgumentAdapter]


@dataclass
class _DocStringFields:
    description: Text
    notes: NotesList
    footnotes: NotesDict


class TaskRegistrationRecord(RegistrationRecord):
    """
    Task registration record.

    Properties are used for data access for the following reasons:
    - Make data effectively read-only.
    - Provide defaults for None values.
    - Postpone building costly derived data that may not always be needed.
    """

    def __init__(self,
                 implementation: TaskImplementation,
                 module: Optional[ModuleType],
                 description: Optional[Text],
                 notes: Optional[NotesList],
                 footnotes: Optional[NotesDict],
                 sub_task_references: Optional[SubTaskCollection],
                 ):
        """
        Task registration constructor.

        :param implementation: task class or function
        :param module: containing module
        :param description: task description
        :param notes: task help notes
        :param footnotes: named footnotes displayed in task help if referenced by "[<name>]"
        :param sub_task_references: sub-task references by name
        """
        if module is None:
            # Not sure why this cast is needed, since TaskImplementation is just
            # an indirect reference to Callable.
            module = sys.modules[cast(implementation, Callable).__module__]
        super().__init__(implementation, module)
        self.description = description
        self.notes = notes
        self.footnotes = footnotes
        self.sub_task_references = _make_sub_tasks_map(sub_task_references)

    @property
    def implementation(self) -> TaskImplementation:
        """
        Registered task implementation.

        :return: implementation reference
        """
        # noinspection PyTypeChecker
        return super().implementation


def _get_default_task_name(reference: TaskReference) -> Text:
    if ismodule(reference):
        return reference.__name__.split('.')[-1]
    if isinstance(reference, str):
        return reference.split('.')[-1]
    name = reference.__name__
    # Strip trailing underscore, which can be used to avoid collisions with built-ins.
    if name.endswith('_'):
        name = name[:-1]
    return name


def _make_sub_tasks_map(raw_tasks: Optional[SubTaskCollection]) -> Optional[SubTaskDict]:
    # None?
    if raw_tasks is None:
        return None
    # Already a dictionary?
    if isinstance(raw_tasks, dict):
        return raw_tasks
    # Convert sequence to dictionary using default names based on references.
    if isinstance(raw_tasks, (list, tuple)):
        return {_get_default_task_name(reference): reference for reference in raw_tasks}
    abort('Assigned tasks are neither a sequence nor a dictionary.', raw_tasks)


class AssignedTask:
    """
    An assigned task adds a name and visibility to registered task data.

    It also provides access to resolved fields and assigned sub-tasks. Text
    items like description, notes, and footnotes are populated as needed with
    default values.
    """

    def __init__(self,
                 registered_task: TaskRegistrationRecord,
                 name: Text,
                 visibility: int,
                 ):
        """
        Construct sub-task.

        :param registered_task: registered task that owns most of the data and some
                                that it can produce on demand
        :param name: task name
        :param visibility: 0=normal, 1=secondary, 2=hidden
        """
        self._registered_task = registered_task
        self.name = name
        self.visibility = visibility
        self._parsed_doc_string_fields: Optional[_DocStringFields] = None
        self._sub_tasks: Optional[List['AssignedTask']] = None
        self._fields: Optional[List[TaskField]] = None

    @property
    def implementation(self) -> TaskImplementation:
        """
        Task implementation.

        :return: implementation class or function
        """
        return self._registered_task.implementation

    @property
    def module(self) -> ModuleType:
        """
        Task module.

        :return: containing module
        """
        return self._registered_task.module

    @property
    def description(self) -> Text:
        """
        Task description.

        :return: description text
        """
        return (self._registered_task.description
                if self._registered_task.description is not None
                else self._doc_string_fields.description)

    @property
    def notes(self) -> NotesList:
        """
        Task description.

        :return: description text
        """
        return (self._registered_task.notes if self._registered_task.notes is not None
                else self._doc_string_fields.notes)

    @property
    def footnotes(self) -> NotesDict:
        """
        Task description.

        :return: description text
        """
        return (self._registered_task.footnotes if self._registered_task.footnotes is not None
                else self._doc_string_fields.footnotes)

    @property
    def sub_tasks(self) -> List['AssignedTask']:
        """
        Assigned sub-task list.

        :return: sub-task list
        """
        if self._sub_tasks is None:
            self._sub_tasks: List[AssignedTask] = []
            if self._registered_task.sub_task_references:
                for ident, task_ref in self._registered_task.sub_task_references.items():
                    ident_match = TASK_IDENT_REGEX.match(ident)
                    if ident_match is None:
                        log_error(f'Bad task identifier "{ident}".')
                        continue
                    name = ident_match.group(1)
                    visibility_spec = ident_match.group(2).lower() if ident_match.group(2) else ''
                    if visibility_spec in ['s', 'secondary']:
                        visibility = 1
                    elif visibility_spec in ['h', 'hidden']:
                        visibility = 2
                    else:
                        visibility = 0
                    assigned_task = TASK_REGISTRY.resolve_assigned_task(
                        task_ref, name, visibility, required=True)
                    self._sub_tasks.append(assigned_task)
        return self._sub_tasks

    @property
    def fields(self) -> List[TaskField]:
        """
        Fields and defaults for task.

        :return: task fields and defaults object
        """
        if self._fields is None:
            if not isfunction(self.implementation):
                abort(f'Task implementation is not a @task function.', self.implementation)
            extracted_fields = get_function_fields(self.implementation)
            errors = extracted_fields.errors
            if (len(extracted_fields.fields) == 0
                    or not issubclass(extracted_fields.fields[0].type_hint,
                                      SelfRegisteringContextBase)):
                abort(f'Task function first argument is not a context.',
                      self.implementation)
            raw_fields = extracted_fields.fields[1:]
        # noinspection PyUnboundLocalVariable
            if errors:
                # noinspection PyUnboundLocalVariable
                abort(f'Bad task {self.full_name} {plural("field", errors)}.', *errors)
            task_fields: List[TaskField] = []
            # noinspection PyUnboundLocalVariable
            for raw_field in raw_fields:
                if not isinstance(raw_field.annotation, Field):
                    abort(f'Not all fields in task {self.full_name} have Jiig field hints.')
                field_annotation: Field = raw_field.annotation
                default = raw_field.default
                if default is None and 'default' in field_annotation.hints:
                    default = DefaultValue(field_annotation.hints['default'])
                if 'repeat' in field_annotation.hints:
                    repeat = Repetition.from_spec(field_annotation.hints['repeat'])
                else:
                    repeat = None
                choices: Optional[List] = field_annotation.hints.get('choices', None)
                task_fields.append(
                    TaskField(raw_field.name,
                              field_annotation.description,
                              raw_field.type_hint,
                              field_annotation.field_type,
                              default,
                              repeat,
                              choices,
                              field_annotation.hints,
                              field_annotation.adapters),
                )
            self._fields = task_fields
        return self._fields

    @property
    def full_name(self):
        """
        Full display name.

        :return: full display name
        """
        return self._registered_task.full_name

    @property
    def _doc_string_fields(self) -> _DocStringFields:
        if self._parsed_doc_string_fields is None:
            self._parsed_doc_string_fields = _parse_doc_string(self.implementation)
        return self._parsed_doc_string_fields


class TaskRegistry(Registry):
    """Task registry."""

    def __init__(self):
        """Task registry constructor."""
        super().__init__('task')

    def register(self, registration: TaskRegistrationRecord):
        """
        Perform task registration.

        :param registration: task registration record
        """
        super().register(registration)

    def resolve(self,
                reference: TaskReference,
                required: bool = False,
                ) -> Optional[TaskRegistrationRecord]:
        """
        Resolve task reference to registration record (if possible).

        Use resolve_assigned_task() instead of resolve() when a task has been
        assigned a name and visibility in the context of a tool or parent task.

        :param reference: module, class, or function reference
        :param required: abort if reference resolution fails
        :return: registration record or None if it couldn't be resolved
        """
        return super().resolve(reference, required=required)

    def resolve_assigned_task(self,
                              reference: TaskReference,
                              name: Text,
                              visibility: int,
                              required: bool = False,
                              ) -> Optional[AssignedTask]:
        """
        Resolve task reference to an AssignedTask (if possible).

        Needed as front end to resolve() method in order to merge data from
        registered task with name and visibility when task has been assigned to
        a tool or parent task.

        :param reference: module, class, or function reference
        :param name: task name
        :param visibility: visibility (0=normal, 1=secondary, 2=hidden)
        :param required: abort if reference resolution fails
        :return: resolved task or None if it wasn't resolved and required is False
        """
        registered_task = self.resolve(reference, required=required)
        # noinspection PyTypeChecker
        return AssignedTask(registered_task, name or '', visibility)

    def is_registered(self, reference: TaskReference) -> bool:
        """
        Test if task reference is registered.

        :param reference: task reference to test
        :return: True if the task reference is registered
        """
        return super().is_registered(reference)

    def guess_root_task_implementation(self,
                                       *additional_packages: str,
                                       ) -> Optional[TaskImplementation]:
        """
        Attempt to guess the root task by finding one with no references.

        The main point is to support the quick start use case, and is not
        intended for long-lived projects. It has the following caveats.

        CAVEAT 1: It produces a heuristic guess (not perfect).
        CAVEAT 2: It is quite inefficient, O(N^2), for large numbers of tasks.
        CAVEAT 3: It only works with registered tasks, and won't find non-loaded ones.

        Caveats aside, it prefers to fail, rather than return a bad root task.

        :param additional_packages: additional package names for resolving named modules
        :return: root task implementation if found, None if not
        """

        # Gather the full initial candidate pool.
        candidates_by_id: Dict[int, TaskRegistrationRecord] = {}
        candidate_ids_by_module_name: Dict[Text, int] = {}
        for item_id, registration in self.by_id.items():
            if not registration.implementation.__module__.startswith('jiig.'):
                # Need to cast to TaskRegistrationRecord (also below).
                candidates_by_id[item_id] = cast(registration, TaskRegistrationRecord)
                candidate_ids_by_module_name[registration.implementation.__module__] = item_id
        if len(candidates_by_id) > 20:
            log_warning('Larger projects should declare an explicit root task.')

        # Reduce candidate pool by looking for references to candidates.
        for registration in self.by_id.values():
            # Remove any candidates that are referenced. Handle module
            # instances, module strings, and function references.
            task_registration = cast(registration, TaskRegistrationRecord)
            for reference in task_registration.tasks.values():
                # Module name?
                if isinstance(reference, str):
                    reference_id = candidate_ids_by_module_name.get(reference)
                    if reference_id is None:
                        for package in additional_packages:
                            module_name = '.'.join([package, reference])
                            reference_id = candidate_ids_by_module_name.get(module_name)
                            if reference_id is not None:
                                break
                # Module instance?
                elif ismodule(reference):
                    reference_id = candidate_ids_by_module_name.get(reference.__name__)
                # @task function?
                else:
                    reference_id = id(reference)
                if reference_id is not None and reference_id in candidates_by_id:
                    del candidates_by_id[reference_id]

        # Wrap-up.
        if len(candidates_by_id) == 0:
            log_error('Root task not found.')
            return None
        if len(candidates_by_id) != 1:
            names = sorted([candidate.full_name for candidate in candidates_by_id.values()])
            log_error(f'More than one root task candidate.', *names)
            return None
        return list(candidates_by_id.values())[0].implementation


TASK_REGISTRY = TaskRegistry()


def _parse_doc_string(implementation: TaskImplementation) -> _DocStringFields:
    footnote_builder = FootnoteBuilder()
    doc_string = implementation.__doc__ or ''
    footnote_builder.parse(doc_string)
    description = DEFAULT_TASK_DESCRIPTION
    notes: NotesList = []
    for paragraph_idx, paragraph in enumerate(footnote_builder.original_body_paragraphs):
        if paragraph_idx == 0:
            description = paragraph
        else:
            notes.append(paragraph)
    return _DocStringFields(description, notes, footnote_builder.footnotes)
