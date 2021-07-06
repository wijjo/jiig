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
