"""
Runner provides data and an API to task call-back functions..
"""

from contextlib import contextmanager
from importlib import import_module
from inspect import isclass, ismodule
from typing import Text, Iterator, Union, Optional, Type

from jiig.driver import Driver, DriverTask
from jiig.registry import register_runtime, RuntimeReference, RuntimeRegistry
from jiig.util.alias_catalog import AliasCatalog, open_alias_catalog
from jiig.util.console import log_error

from .runtime_context import RuntimeContext
from .runtime_task import RuntimeTask
from .runtime_tool import RuntimeTool

RuntimeContextReference = Union[RuntimeContext, Text, object]


class Runtime(RuntimeContext):
    """Application runtime data and options."""

    """
    Application Runtime class.

    Can also use as a base for registered custom runtime classes.

    Self-registers to the runtime registry.

    The class declaration accepts no keyword arguments.
    """

    def __init_subclass__(cls, /, **kwargs):
        """Self-register Runtime subclasses."""
        super().__init_subclass__(**kwargs)
        register_runtime(cls)

    def __init__(self,
                 tool: RuntimeTool,
                 root_task: RuntimeTask,
                 driver_root_task: DriverTask,
                 driver: Driver,
                 data: object,
                 **kwargs,
                 ):
        """
        Construct root runtime context.

        Passed to Task call-back methods to provide a runtime API and text
        symbol expansion.

        :param tool: tool data
        :param root_task: active root task
        :param driver_root_task: active root task used by driver
        :param driver: active Jiig interface driver
        :param data: parsed command line argument data
        :param kwargs: initial symbols
        """
        self.tool = tool
        self.root_task = root_task
        self.driver_root_task = driver_root_task
        self.driver = driver
        self.data = data
        super().__init__(
            None,
            aliases_path=tool.aliases_path,
            author=tool.author,
            build_folder=tool.build_folder,
            copyright=tool.copyright,
            description=tool.description,
            doc_folder=tool.doc_folder,
            jiig_library_folder=tool.jiig_library_folder,
            jiig_root_folder=tool.jiig_root_folder,
            pip_packages=tool.pip_packages,
            project_name=tool.project_name,
            sub_task_label=tool.sub_task_label,
            tool_name=tool.name,
            tool_root_folder=tool.tool_root_folder,
            top_task_label=tool.top_task_label,
            venv_folder=tool.venv_folder,
            version=tool.version,
            **kwargs,
        )

    @contextmanager
    def open_alias_catalog(self) -> Iterator[AliasCatalog]:
        """
        Open alias catalog.

        For use in a `with` block to automatically close the catalog.

        :return: catalog
        """
        with open_alias_catalog(self.tool.name, self.tool.aliases_path) as catalog:
            yield catalog

    def provide_help(self, *names: Text, show_hidden: bool = False):
        """
        Provide help output.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        self.driver.provide_help(self.driver_root_task, *names, show_hidden=show_hidden)

    @classmethod
    def resolve(cls,
                runtime_ref: RuntimeReference,
                ) -> Optional[Type['Runtime']]:
        """
        Resolve a runtime reference to a Runtime class (if possible).

        :param runtime_ref: runtime reference
        :return: Runtime class if resolved or None otherwise
        """
        # Reference is a module name? Convert the reference to a loaded module.
        if isinstance(runtime_ref, str):
            try:
                runtime_ref = import_module(runtime_ref)
            except Exception as exc:
                log_error(f'Failed to load runtime module.',
                          exc, module_name=runtime_ref, exception_traceback=True)
                return None
        # Reference is a module? Convert the reference to a Runtime class.
        if ismodule(runtime_ref):
            runtime_spec = RuntimeRegistry.by_module_id.get(id(runtime_ref))
            if runtime_spec is None:
                log_error(f'Failed to resolve unregistered runtime module'
                          f' {runtime_ref.__name__} (id={id(runtime_ref)}).')
                return None
            runtime_ref = runtime_spec.runtime_class
        # Reference is a class? Hopefully it's one that was registered.
        if not isclass(runtime_ref):
            log_error('Bad runtime reference.', runtime_ref)
            return None
        runtime_spec = RuntimeRegistry.by_class_id.get(id(runtime_ref))
        if not runtime_spec:
            log_error('Runtime reference not found for class.', runtime_ref)
            return None
        if not issubclass(runtime_spec.runtime_class, Runtime):
            log_error(f'Registered runtime {runtime_ref} is not Runtime subclass.')
            return None
        return runtime_spec.runtime_class
