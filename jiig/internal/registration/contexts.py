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

"""
Context registry.

Uses common Registry support, but adds data to the registration record and
provides a more type-specific API for accessing and querying the registry.
"""
from typing import Type
from types import ModuleType

from jiig.action_context import ActionContext

from jiig.registry import RegistrationRecord, Registry

ContextReference = Type[ActionContext] | str | ModuleType


class ContextRegistrationRecord(RegistrationRecord):
    """Type-safe context RegistrationRecord subclass."""

    @property
    def implementation(self) -> Type[ActionContext]:
        """
        Registered context implementation.

        :return: implementation reference
        """
        # noinspection PyTypeChecker
        return super().implementation


class ContextRegistry(Registry):
    """Context registry."""

    def __init__(self):
        """Context registry constructor."""
        super().__init__('context')

    def register(self, registration: ContextRegistrationRecord):
        """
        Perform registration.

        :param registration: registration record
        """
        super().register(registration)

    def resolve(self,
                reference: ContextReference,
                required: bool = False,
                ) -> ContextRegistrationRecord | None:
        """
        Resolve reference to registration record (if possible).

        :param reference: module, class, or function reference
        :param required: abort if reference resolution fails
        :return: registration record or None if it couldn't be resolved
        """
        return super().resolve(reference, required=required)

    def is_registered(self, reference: ContextReference) -> bool:
        """
        Test if reference is registered.

        :param reference: reference to test
        :return: True if the task reference is registered
        """
        return super().is_registered(reference)


CONTEXT_REGISTRY = ContextRegistry()