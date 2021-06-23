"""Generic registry class."""

import sys
from importlib import import_module
from inspect import ismodule, isclass
from typing import Dict, Type, TypeVar, Union, Text, Optional, Generic

from jiig.util.console import abort, log_error

T_registration = TypeVar('T_registration')
T_registered = TypeVar('T_registered')


class Registration(Generic[T_registered]):

    # Reference to registered class, module name, or loaded module, with `object`
    # representing loaded module, due to lack of better alternative.
    Reference = Union[Type[T_registered], Text, object]

    def __init__(self, registered_class: Type[T_registered]):
        self.registered_class = registered_class


class Registry(Generic[T_registration, T_registered]):
    """Registry indexed by module and class ID."""

    # Reference to registered class, module name, or loaded module, with `object`
    # representing loaded module, due to lack of better alternative.
    Reference = Union[Type[T_registered], Text, object]

    def __init__(self, name: Text):
        self.name = name
        self.by_module_id: Dict[int, T_registration] = {}
        self.by_class_id: Dict[int, T_registration] = {}

    def register(self, registration: T_registration):
        """
        Perform registration.

        :param registration: registration object
        """
        self.by_module_id[id(sys.modules[registration.registered_class.__module__])] = registration
        self.by_class_id[id(registration.registered_class)] = registration

    def resolve(self,
                reference: Reference,
                required: bool = False,
                ) -> Optional[T_registration]:
        """
        Resolve reference to registration object (if possible).

        :param reference: module or class reference
        :param required: abort if reference resolution fails
        :return: registration object or None if it couldn't be resolved
        """
        error_function = abort if required else log_error
        # Convert named module reference to loaded module?
        if isinstance(reference, str):
            try:
                reference = import_module(reference)
            except Exception as exc:
                error_function(f'Failed to load {self.name} module: {reference}',
                               exc,
                               exception_traceback=True)
                return None
        # Convert module reference to class?
        if ismodule(reference):
            registration = self.by_module_id.get(id(reference))
            if registration is None:
                error_function(f'Failed to resolve unregistered {self.name} module'
                               f' {reference.__name__} (id={id(reference)}).')
                return None
            reference = registration.registered_class
        # Hopefully class has been registered.
        if not isclass(reference):
            error_function(f'Bad {self.name} reference.', reference)
            return None
        registration = self.by_class_id.get(id(reference))
        if not registration:
            error_function(f'Reference not found for {self.name} class.', reference)
            return None
        return registration
