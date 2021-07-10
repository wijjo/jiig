"""Driver task class."""

from dataclasses import dataclass
from typing import Text, List, Any, Dict, Optional, Sequence

from ..util.footnotes import NotesList, NotesDict
from ..util.general import DefaultValue
from ..util.repetition import Repetition

from .driver_field import DriverField


@dataclass
class DriverTask:
    """Task data fed to driver."""
    name: Text
    description: Text
    sub_tasks: List['DriverTask']
    fields: List[DriverField]
    notes: NotesList
    footnotes: NotesDict
    visibility: int
    hints: Dict

    def add_sub_task(self,
                     name: Text,
                     description: Text,
                     notes: NotesList,
                     footnotes: NotesDict,
                     visibility: int,
                     hints: Dict,
                     ) -> 'DriverTask':
        """
        Add sub-task data.

        :param name: sub-task name
        :param description: sub-task description
        :param notes: task notes list
        :param footnotes: task footnotes dictionary
        :param visibility: 0=normal, 1=secondary, 2=hidden
        :param hints: raw hint dictionary
        :return: new sub-task
        """
        sub_task = DriverTask(name, description, [], [], notes, footnotes, visibility, hints)
        self.sub_tasks.append(sub_task)
        return sub_task

    def add_field(self,
                  name: Text,
                  description: Text,
                  element_type: Any,
                  repeat: Optional[Repetition] = None,
                  default: Optional[DefaultValue] = None,
                  choices: Optional[Sequence] = None,
                  ):
        """
        Add task field data.

        :param name: field name
        :param description: field description
        :param element_type: field element type
        :param repeat: optional repeat min/max
        :param default: optional default value
        :param choices: optional value choice list
        """
        self.fields.append(DriverField(name=name,
                                       description=description,
                                       element_type=element_type,
                                       repeat=repeat,
                                       default=default,
                                       choices=choices))

    def resolve_task_stack(self, names: Sequence[Text]) -> Optional[List['DriverTask']]:
        """
        Get task stack (list) based on names list.

        :param names: name stack as list
        :return: sub-task stack as list or None if it fails to resolve
        """
        def _resolve_sub_stack(task: 'DriverTask',
                               sub_names: Sequence[Text],
                               ) -> List['DriverTask']:
            for sub_task in task.sub_tasks:
                if sub_task.name == sub_names[0]:
                    if len(sub_names) == 1:
                        return [sub_task]
                    return [sub_task] + _resolve_sub_stack(sub_task, sub_names[1:])
            raise ValueError(names[0])
        try:
            return _resolve_sub_stack(self, names)
        except ValueError:
            return None
