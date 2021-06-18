"""Runtime registry."""

import sys
from typing import Type, Dict

from .runtime_specification import RuntimeSpecification


class RuntimeRegistry:
    """Registered runtime specifications indexed by module and class ID."""
    by_module_id: Dict[int, RuntimeSpecification] = {}
    by_class_id: Dict[int, RuntimeSpecification] = {}


def register_runtime(cls: Type):
    """
    Register a Runtime class.

    :param cls: class type to register
    """
    runtime_spec = RuntimeSpecification(runtime_class=cls)
    RuntimeRegistry.by_module_id[id(sys.modules[cls.__module__])] = runtime_spec
    RuntimeRegistry.by_class_id[id(cls)] = runtime_spec
