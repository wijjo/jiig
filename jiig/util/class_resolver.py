# Copyright (C) 2021-2023, Steven Cooper
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

"""Class resolver utility."""

import sys
from dataclasses import dataclass
from inspect import isclass, ismodule
from types import ModuleType
from typing import TypeVar, Generic

from .log import abort, log_error
from .python import ModuleReferenceResolver


ST = TypeVar('ST')


class ClassResolver(Generic[ST]):
    """Resolves class reference (module name, module string, or class),"""

    @dataclass
    class ResolvedClass:
        """Successful class resolution data."""
        subclass: type[ST]
        module: ModuleType

    @dataclass
    class ResolvedInstance:
        """Successful instance resolution data."""
        instance: ST
        module: ModuleType

    def __init__(self,
                 base_class_type: type[ST],
                 name: str,
                 ):
        """
        ResolvedClass constructor.

        Args:
            base_class_type: expected base class for resolved references
            name: human-friendly name for logged messages
        """
        self.base_class_type = base_class_type
        self.base_class_type_name = '.'.join([base_class_type.__module__,
                                              base_class_type.__name__]),
        self.name = name
        self.module_resolver = ModuleReferenceResolver()

    def resolve_class(self,
                      reference: type[ST] | str | ModuleType,
                      ) -> ResolvedClass:
        found_class: type[ST] | None = None
        # Resolve class type directly?
        if isclass(reference):
            if issubclass(reference, self.base_class_type):
                found_class = reference
        else:
            # Resolve string (module package name) reference to module?
            if isinstance(reference, str):
                reference = self.module_resolver.resolve(reference)
            # Resolve module to first declared subclass in that module?
            if reference is not None and ismodule(reference):
                for module_attr_name, module_attr in reference.__dict__.items():
                    if not module_attr_name.startswith('_') and isclass(module_attr):
                        if module_attr.__module__ == reference.__name__:
                            if issubclass(module_attr, self.base_class_type):
                                found_class = module_attr
                                break
                else:
                    log_error(f'Module has no {self.name}: {reference.__package__}')
        if found_class is None:
            abort(f'Failed to resolve reference as {self.name} class:',
                  target=str(reference),
                  type=self.base_class_type_name)
        return self.ResolvedClass(found_class, sys.modules[found_class.__module__])

    def resolve_instance(self,
                         reference: ST | str | ModuleType,
                         ) -> ResolvedInstance:
        found_instance: ST | None = None
        if isinstance(reference, self.base_class_type):
            found_instance = reference
        else:
            # Resolve string (module package name) reference to module?
            if isinstance(reference, str):
                reference = self.module_resolver.resolve(reference)
            # Resolve module to first declared subclass in that module?
            if reference is not None and ismodule(reference):
                for module_attr_name, module_attr in reference.__dict__.items():
                    if (not module_attr_name.startswith('_')
                            and isinstance(module_attr, self.base_class_type)):
                        found_instance = module_attr
                        break
                else:
                    log_error(f'Module has no {self.base_class_type.__name__} instance.')
        if found_instance is None:
            abort(f'Failed to resolve reference as {self.name} instance:',
                  target=str(reference),
                  type=self.base_class_type_name)
        return self.ResolvedInstance(
            found_instance, sys.modules[found_instance.__class__.__module__])
