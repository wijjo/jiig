"""Generic registry class."""
import sys
from importlib import import_module
from inspect import ismodule, isfunction
from typing import Dict, Type, Union, Text, Optional, Callable
from types import ModuleType

from ..util.log import abort, log_error

# Reference to registered class, module name, loaded module, or function.
RegisteredReference = Union[Type, Text, ModuleType, Callable]
RegisteredImplementation = Union[Type, Callable]


def full_implementation_name(implementation: RegisteredImplementation) -> Text:
    """
    Full name as <module>.<name>.

    :return: full name
    """
    module_name = implementation.__module__
    if module_name == 'builtins':
        module_name = '<tool>'
    return f'{module_name}.{implementation.__name__}' \
           f'{"()" if isfunction(implementation) else ""}'


class RegistrationRecord:
    """Base class for registration data record."""
    def __init__(self, implementation: RegisteredImplementation,
                 module: ModuleType,
                 ):
        """
        Registration record constructor.

        :param implementation: implementation class or function
        :param module: containing module
        """
        self._implementation = implementation
        self.module = module

    @property
    def implementation(self) -> RegisteredImplementation:
        """
        Registered implementation.

        Implemented as property to make read-only and to allow more
        type-specific subclass overrides.

        :return: implementation reference
        """
        return self._implementation

    @property
    def full_name(self) -> Text:
        """
        Full name as <module>.<name>.

        :return: full name
        """
        return full_implementation_name(self.implementation)


class Registry:
    """
    Registry indexed by module and class or function ID.

    Note that this base registry class does not care if the registered item is a
    class or a function.
    """

    def __init__(self, name: Text):
        """
        Registry constructor.

        :param name: registry name
        """
        self.name = name
        self.by_id: Dict[int, RegistrationRecord] = {}
        self.by_module_id: Dict[int, RegistrationRecord] = {}

    def register(self, registration: RegistrationRecord):
        """
        Perform registration.

        :param registration: registration record
        """
        self.by_id[id(registration.implementation)] = registration
        self.by_module_id[id(registration.module)] = registration

    def resolve(self,
                reference: RegisteredReference,
                required: bool = False,
                ) -> Optional[RegistrationRecord]:
        """
        Resolve reference to registration record (if possible).

        :param reference: module, class, or function reference
        :param required: abort if reference resolution fails
        :return: registration record or None if it couldn't be resolved
        """
        error_function = abort if required else log_error
        # Resolve string (module package name) reference to loaded module?
        if isinstance(reference, str):
            try:
                reference = import_module(reference)
            except Exception as exc:
                error_function(f'Failed to load {self.name} module: {reference}',
                               exc,
                               exception_traceback=True,
                               exception_traceback_skip=2,
                               skip_non_source_frames=True)
                return None
        # Resolve module reference?
        if ismodule(reference):
            registration = self.by_module_id.get(id(reference))
        # Resolve item reference (i.e. class or function)?
        else:
            registration = self.by_id.get(id(reference))
        if registration is None:
            error_function(f'Failed to resolve {self.name}: {reference.__name__}')
            return None
        return registration

    def is_registered(self, reference: RegisteredReference) -> bool:
        """
        Test if a reference is registered.

        :param reference: reference to test
        :return: True if the reference is registered
        """
        if isinstance(reference, str):
            return reference in sys.modules and id(sys.modules[reference]) in self.by_module_id
        if ismodule(reference):
            return id(reference) in self.by_module_id
        return id(reference) in self.by_id
