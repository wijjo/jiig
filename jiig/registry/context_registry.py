"""
Runtime registry.
"""

from typing import TypeVar

from ._registry import Registration, Registry

T_context = TypeVar('T_context')


class ContextRegistration(Registration[T_context]):
    """Registered context."""
    pass


class RegisteredContext:
    """Self-registering action context class."""
    def __init_subclass__(cls, /, **kwargs):
        """Self-register Runtime subclasses."""
        super().__init_subclass__(**kwargs)
        CONTEXT_REGISTRY.register(ContextRegistration(cls))


class ContextRegistry(Registry[ContextRegistration, RegisteredContext]):
    """Registered contexts indexed by module and class ID."""
    pass


CONTEXT_REGISTRY = ContextRegistry('context')
