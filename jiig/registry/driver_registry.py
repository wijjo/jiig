"""
Driver registry.
"""

from typing import TypeVar

from ._registry import Registration, Registry

T_driver = TypeVar('T_driver')


class DriverRegistration(Registration[T_driver]):
    """Registered driver."""
    pass


class RegisteredDriver:
    """Self-registering action context class."""
    def __init_subclass__(cls, /, **kwargs):
        """Self-register Runtime subclasses."""
        super().__init_subclass__(**kwargs)
        DRIVER_REGISTRY.register(DriverRegistration(cls))


class DriverRegistry(Registry[DriverRegistration, RegisteredDriver]):
    """Registered drivers indexed by module and class ID."""
    pass


DRIVER_REGISTRY = DriverRegistry('driver')
