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

"""Runner provides data and an API to task call-back functions.."""
import sys
from pathlib import Path
from typing import (
    Any,
    Callable,
    Self,
    Sequence,
)

from .constants import (
    DEFAULT_BUILD_FOLDER_NAME,
    DEFAULT_DOC_FOLDER_NAME,
    DEFAULT_TESTS_FOLDER_NAME,
)
from .context import (
    ActionContext,
    Context,
)
from .driver import (
    Driver,
    DriverAppData,
    DriverArgumentCheckData,
    DriverOptions,
    DriverPreliminaryAppData,
)
from .task import RuntimeTask
from .types import (
    RuntimeHelpGenerator,
    ToolMetadata,
    ToolPaths,
)
from .util.log import LogWriter
from .util.process import shell_command_string
from .util.scoped_catalog import ScopedCatalog


class _RuntimeInternal:
    def __init__(self,
                 driver: Driver,
                 root_task: RuntimeTask,
                 aliases_catalog: ScopedCatalog,
                 params_catalog: ScopedCatalog,
                 ):
        self.driver = driver
        self.root_task = root_task
        self.aliases_catalog = aliases_catalog
        self.params_catalog = params_catalog


class Runtime(ActionContext):
    """Application Runtime class.

    This is the top level context presented to task call-back methods.

    Can also use as a base for registered custom runtime classes.

    Self-registers sub-classes to the context registry.

    The class declaration accepts no keyword arguments.
    """

    def __init__(self,
                 parent: Context | None,
                 help_generator: RuntimeHelpGenerator,
                 data: object,
                 meta: ToolMetadata,
                 paths: ToolPaths,
                 aliases_catalog: ScopedCatalog,
                 params_catalog: ScopedCatalog,
                 driver: Driver,
                 root_task: RuntimeTask,
                 **symbols,
                 ):
        """Construct root runtime context.

        Passed to Task call-back methods to provide a runtime API and text
        symbol expansion.

        Args:
            parent: optional parent context
            tool: tool data
            help_generator: on-demand help generator
            data: parsed command line argument data
            meta: runtime metadata
            paths: runtime paths
            aliases_catalog: aliases scoped catalog
            params_catalog: tool parameters scoped catalog
            driver: jiig driver, used internally
            root_task: root task for re-parsing command line arguments, used internally
            **symbols: initial symbols
        """
        self.help_generator = help_generator
        self.data = data
        self.meta = meta
        self.paths = paths
        self.internal = _RuntimeInternal(driver, root_task, aliases_catalog, params_catalog)
        self.when_done_callables: list[Callable] = []
        super().__init__(
            parent,
            aliases_path=paths.aliases_catalog_path,
            author=meta.author,
            build_folder=paths.build,
            copyright=meta.copyright,
            description=meta.description,
            doc_folder=paths.doc,
            pip_packages=meta.pip_packages,
            project_name=meta.project_name,
            sub_task_label=meta.sub_task_label,
            tool_name=meta.tool_name,
            top_task_label=meta.top_task_label,
            venv_folder=paths.venv,
            version=meta.version,
            **symbols,
        )

    def when_done(self, when_done_callable: Callable):
        """Register "when-done" clean-up call-back.

        When-done callables are called in LIFO (last in/first out) order.

        When-done callables must accept no arguments. They are generally
        implemented as inner functions within the task run function, and are
        aware of the local stack frame and runtime.

        Args:
            when_done_callable: callable (accepts no arguments) that is called
                when done
        """
        self.when_done_callables.insert(0, when_done_callable)

    def get_param(self, name: str) -> Any:
        """Get named tool parameter value.

        Args:
            name: parameter name

        Returns:
            parameters dictionary
        """
        if not self.internal.params_catalog.exists(name):
            self.error(f'Unknown parameter name: {name}')
            return None
        result = self.internal.params_catalog.get(name)
        return result.found_payload

    def provide_help(self, *names: str, show_hidden: bool = False):
        """Provide help output.

        Args:
            *names: name parts (task name stack)
            show_hidden: show hidden task help if True
        """
        self.help_generator.generate_help(*names, show_hidden=show_hidden)

    def context(self, **symbols) -> Self:
        """Create a runtime sub-context.

        Args:
            **symbols: sub-context symbols

        Returns:
            runtime sub-context
        """
        return self.__class__(parent=self,
                              help_generator=self.help_generator,
                              data=self.data,
                              meta=self.meta,
                              paths=self.paths,
                              aliases_catalog=self.internal.aliases_catalog,
                              params_catalog=self.internal.params_catalog,
                              driver=self.internal.driver,
                              **symbols)


class TestLogWriter(LogWriter):
    """Log writer for testing."""
    def write_line(self, text: str, is_error: bool = False, extra_space: bool = False):
        pass


class TestDriver(Driver):
    """Driver for testing."""

    def on_initialize_driver(self,
                             command_line_arguments: Sequence[str],
                             ) -> DriverPreliminaryAppData:
        return DriverPreliminaryAppData(None, [])

    def on_check_arguments(self,
                           command_line_arguments: Sequence[str],
                           ) -> DriverArgumentCheckData:
        return DriverArgumentCheckData(None, [], [], None)

    def on_initialize_application(self,
                                  arguments: list[str],
                                  root_task: RuntimeTask,
                                  ) -> DriverAppData:
        return DriverAppData(None, [], [], [])

    def on_provide_help(self,
                        root_task: RuntimeTask,
                        names: list[str],
                        show_hidden: bool,
                        ):
        pass

    def get_log_writer(self) -> LogWriter:
        return TestLogWriter()


class TestRuntime(Runtime):
    """Runtime for testing."""
    def __init__(self, base_folder: str | Path):
        meta = ToolMetadata('test')
        if isinstance(base_folder, str):
            base_folder = Path(base_folder)

        class TestAliasesCatalog(ScopedCatalog):
            """Scoped aliases catalog class for testing."""
            path = meta.aliases_catalog_path
            item_label = 'test alias'
            payload_label = 'test alias command'
            payload_label_plural = 'test alias commands'

            def payload_formatter(self, name: str, payload: Any):
                return shell_command_string(*payload)

        class TestParamsCatalog(ScopedCatalog):
            """Scoped parameters catalog class for testing."""
            path = meta.params_catalog_path
            item_label = 'test parameter'
            payload_label = 'test parameter value'
            payload_label_plural = 'test parameter values'
            locked = True

        super().__init__(
            parent=None,
            help_generator=TestHelpGenerator(),
            data=TestData(),
            meta=meta,
            paths=ToolPaths(
                venv=Path(sys.executable).parent.parent,
                base_folder=base_folder,
                aliases_catalog_path=meta.aliases_catalog_path,
                params_catalog_path=meta.params_catalog_path,
                build=base_folder / DEFAULT_BUILD_FOLDER_NAME,
                doc=base_folder / DEFAULT_DOC_FOLDER_NAME,
                test=base_folder / DEFAULT_TESTS_FOLDER_NAME,
            ),
            aliases_catalog=TestAliasesCatalog(),
            params_catalog=TestParamsCatalog(),
            driver=TestDriver('test', 'test driver', DriverOptions()),
            root_task=RuntimeTask('(root)', '(root)', 0, 'test root task'),
        )


class TestHelpGenerator(RuntimeHelpGenerator):
    """Help generator for testing."""
    def generate_help(self, *names: str, show_hidden: bool = False):
        pass


class TestData:
    """Data object for testing."""
    pass
