# Copyright (C) 2021-2022, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

"""CLI hints."""

from typing import Text, List, Dict, Optional, Union

from ...util.general import make_list
from ...util.log import log_error

CLI_HINT_ROOT_NAME = 'cli'
CLI_HINT_OPTIONS = 'options'
CLI_HINT_TRAILING = 'trailing'


class _Uninitialized:
    pass


_UNINITIALIZED = _Uninitialized()


class CLITaskHintRegistrar:

    def __init__(self, registry: 'CLIHintRegistry', full_name: Text):
        self.registry = registry
        self.full_name = full_name
        self._trailing_field: Union[_Uninitialized, Optional[Text]] = _UNINITIALIZED
        self._options_by_field: Union[_Uninitialized, Dict[Text, List[Text]]] = _UNINITIALIZED

    def sub_registrar(self, sub_task_name: Text) -> 'CLITaskHintRegistrar':
        if not self.full_name:
            return self.__class__(self.registry, sub_task_name)
        return self.__class__(self.registry, '.'.join([self.full_name, sub_task_name]))

    @property
    def trailing_field(self) -> Optional[Text]:
        if self._trailing_field is _UNINITIALIZED:
            self._trailing_field = self.registry.trailing_by_task.get(self.full_name)
        return self._trailing_field

    @property
    def options_by_field(self) -> Dict[Text, List[Text]]:
        if self._options_by_field is _UNINITIALIZED:
            self._options_by_field = self.registry.options_by_task.get(self.full_name, {})
        return self._options_by_field

    def set_hints(self, hints: Optional[Dict]):
        if not hints:
            return
        root_hints = hints.get(CLI_HINT_ROOT_NAME)
        if not root_hints:
            return
        if not isinstance(root_hints, dict):
            log_error(f'hints[{CLI_HINT_ROOT_NAME}] is not a dictionary.', root_hints)
            return
        option_hints = root_hints.get(CLI_HINT_OPTIONS)
        if option_hints:
            if isinstance(option_hints, dict):
                for field_name, raw_flags in option_hints.items():
                    flag_list = make_list(raw_flags)
                    if flag_list:
                        if self.full_name not in self.registry.options_by_task:
                            self.registry.options_by_task[self.full_name] = {}
                        self.registry.options_by_task[self.full_name][field_name] = flag_list
            else:
                log_error(f'hints[{CLI_HINT_ROOT_NAME}][{CLI_HINT_OPTIONS}]'
                          f' is not a dictionary.', root_hints)
        trailing_field = root_hints.get(CLI_HINT_TRAILING)
        if trailing_field:
            self.registry.trailing_by_task[self.full_name] = trailing_field


class CLIHintRegistry:

    def __init__(self):
        self.trailing_by_task: Dict[Text, Text] = {}
        self.options_by_task: Dict[Text, Dict[Text, List[Text]]] = {}

    def registrar(self, *names: Text) -> CLITaskHintRegistrar:
        full_name = '.'.join(names)
        return CLITaskHintRegistrar(self, full_name)
