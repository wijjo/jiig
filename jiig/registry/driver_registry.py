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
Driver registry.
"""
import sys
from typing import Union, Type, Text, Optional
from types import ModuleType

from ._registry import RegistrationRecord, Registry

DriverReference = Union[Type['SelfRegisteringDriverBase'], Text, ModuleType]
DriverImplementation = Type['SelfRegisteringContextBase']


class DriverRegistrationRecord(RegistrationRecord):
    """Type-safe driver RegistrationRecord subclass."""

    @property
    def implementation(self) -> DriverImplementation:
        """
        Registered context implementation.

        :return: implementation reference
        """
        # noinspection PyTypeChecker
        return super().implementation


class SelfRegisteringDriverBase:
    """Self-registering action context class."""
    def __init_subclass__(cls, /, **kwargs):
        """Self-register Runtime subclasses."""
        skip_registration = kwargs.pop('skip_registration', False)
        super().__init_subclass__(**kwargs)
        if not skip_registration:
            DRIVER_REGISTRY.register(
                DriverRegistrationRecord(cls, sys.modules[cls.__module__]))


class DriverRegistry(Registry):
    """Driver registry."""

    def __init__(self):
        """Driver registry constructor."""
        super().__init__('driver')

    def register(self, registration: DriverRegistrationRecord):
        """
        Perform registration.

        :param registration: registration record
        """
        super().register(registration)

    def resolve(self,
                reference: DriverReference,
                required: bool = False,
                ) -> Optional[DriverRegistrationRecord]:
        """
        Resolve reference to registration record (if possible).

        :param reference: module, class, or function reference
        :param required: abort if reference resolution fails
        :return: registration record or None if it couldn't be resolved
        """
        return super().resolve(reference, required=required)

    def is_registered(self, reference: DriverReference) -> bool:
        """
        Test if reference is registered.

        :param reference: reference to test
        :return: True if the task reference is registered
        """
        return super().is_registered(reference)


DRIVER_REGISTRY = DriverRegistry()
