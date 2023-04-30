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

from contextlib import contextmanager
from typing import (
    Iterator,
    Callable,
)

from .context import (
    ActionContext,
    Context,
)
from .types import (
    RuntimeHelpGenerator,
    ToolMetadata,
    ToolPaths,
)
from .util.alias_catalog import (
    AliasCatalog,
    open_alias_catalog,
)


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
                 **kwargs,
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
            **kwargs: initial symbols
        """
        self.help_generator = help_generator
        self.data = data
        self.meta = meta
        self.paths = paths
        self.when_done_callables: list[Callable] = []
        super().__init__(
            parent,
            aliases_path=paths.aliases,
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
            **kwargs,
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

    @contextmanager
    def open_alias_catalog(self) -> Iterator[AliasCatalog]:
        """Open alias catalog.

        For use in a `with` block to automatically close the catalog.

        Returns:
            catalog
        """
        with open_alias_catalog(self.meta.tool_name, self.paths.aliases) as catalog:
            yield catalog

    def provide_help(self, *names: str, show_hidden: bool = False):
        """Provide help output.

        Args:
            *names: name parts (task name stack)
            show_hidden: show hidden task help if True
        """
        self.help_generator.generate_help(*names, show_hidden=show_hidden)

    def context(self, **kwargs) -> 'Runtime':
        """Create a runtime sub-context.

        Args:
            **kwargs: sub-context symbols

        Returns:
            runtime sub-context
        """
        return Runtime(self,
                       self.help_generator,
                       self.data,
                       **kwargs)
