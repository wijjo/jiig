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
Runner provides data and an API to task call-back functions..
"""

import os
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Callable

from .action_context import ActionContext
from .context import Context
from .util.alias_catalog import AliasCatalog, open_alias_catalog
from .util.network import resolve_ip_address, get_client_name


class RuntimeHelpGenerator(ABC):
    """Abstract base class implemented by a driver to generate on-demand help output."""

    @abstractmethod
    def generate_help(self, *names: str, show_hidden: bool = False):
        """
        Provide help output.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        ...


@dataclass
class RuntimeMetadata:
    """Runtime metadata."""
    tool_name: str
    project_name: str
    author: str
    copyright: str
    description: str
    version: str
    top_task_label: str
    sub_task_label: str
    pip_packages: list[str]
    doc_api_packages: list[str]
    doc_api_packages_excluded: list[str]


@dataclass
class RuntimePaths:
    """Runtime folder paths."""
    jiig_library: Path
    jiig_root: Path
    tool_root: Path
    libraries: list[Path]
    venv: Path
    aliases: Path
    build: Path
    doc: Path
    test: Path

    @property
    def library_path(self) -> str:
        """
        Provide library path string based on library folders.

        :return: library path string
        """
        return os.pathsep.join([str(p) for p in self.libraries])


class Runtime(ActionContext):
    """
    Application Runtime class.

    This is the top level context presented to task call-back methods.

    Can also use as a base for registered custom runtime classes.

    Self-registers sub-classes to the context registry.

    The class declaration accepts no keyword arguments.
    """

    def __init__(self,
                 parent: Context | None,
                 help_generator: RuntimeHelpGenerator,
                 data: object,
                 meta: RuntimeMetadata,
                 paths: RuntimePaths,
                 **kwargs,
                 ):
        """
        Construct root runtime context.

        Passed to Task call-back methods to provide a runtime API and text
        symbol expansion.

        :param parent: optional parent context
        :param tool: tool data
        :param help_generator: on-demand help generator
        :param data: parsed command line argument data
        :param meta: runtime metadata
        :param paths: runtime paths
        :param kwargs: initial symbols
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
            jiig_library_folder=paths.jiig_library,
            jiig_root_folder=paths.jiig_root,
            pip_packages=meta.pip_packages,
            project_name=meta.project_name,
            sub_task_label=meta.sub_task_label,
            tool_name=meta.tool_name,
            tool_root_folder=paths.tool_root,
            top_task_label=meta.top_task_label,
            venv_folder=paths.venv,
            version=meta.version,
            **kwargs,
        )

    def when_done(self, when_done_callable: Callable):
        """
        Register "when-done" clean-up call-back.

        When-done callables are called in LIFO (last in/first out) order.

        When-done callables must accept no arguments. They are generally
        implemented as inner functions within the task run function, and are
        aware of the local stack frame and runtime.

        :param when_done_callable: callable (accepts no arguments) that is called when done
        """
        self.when_done_callables.insert(0, when_done_callable)

    @contextmanager
    def open_alias_catalog(self) -> Iterator[AliasCatalog]:
        """
        Open alias catalog.

        For use in a `with` block to automatically close the catalog.

        :return: catalog
        """
        with open_alias_catalog(self.meta.tool_name, self.paths.aliases) as catalog:
            yield catalog

    def provide_help(self, *names: str, show_hidden: bool = False):
        """
        Provide help output.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        self.help_generator.generate_help(*names, show_hidden=show_hidden)

    def host_context(self,
                     host: str,
                     host_ip: str = None,
                     user: str = None,
                     home_folder: str = None,
                     client_ssh_key_name: str = None,
                     host_ssh_source_key_name: str = None,
                     client: str = None,
                     ) -> ActionContext:
        """
        Construct new child context with symbols relevant to host connections.

        To avoid confusion with host-related keywords, **kwargs is not supported
        here. Use a sub-context or call update() to add more symbols.

        :param host: host name
        :param host_ip: optional host address (default: queried at runtime)
        :param user: optional user name (default: local client user)
        :param home_folder: optional home folder (default: /home/{user})
        :param client_ssh_key_name: optional client SSH key file base name (default: id_rsa_client)
        :param host_ssh_source_key_name: optional host SSH source key file base name (default: id_rsa_host)
        :param client: optional client name (default: queried at runtime)
        """
        if user is None:
            user = os.environ['USER']
        host_string = f'{user}@{host}'
        if home_folder is None:
            home_folder = f'/home/{user}'
        if host_ip is None:
            host_ip = resolve_ip_address(host)
            if host_ip is None:
                self.abort(f'Unable to resolve host "{host}" IP address for host context.')
        if client is None:
            client = get_client_name()
        if client_ssh_key_name is None:
            client_ssh_key_name = 'id_rsa_client'
        if host_ssh_source_key_name is None:
            host_ssh_source_key_name = 'id_rsa_host'
        client_ssh_key = os.path.expanduser(f'~/.ssh/{client_ssh_key_name}')
        host_ssh_source_key = os.path.expanduser(f'~/.ssh/{host_ssh_source_key_name}')
        return Runtime(self,
                       self.help_generator,
                       self.data,
                       self.meta,
                       self.paths,
                       host=host,
                       host_ip=host_ip,
                       host_string=host_string,
                       client=client,
                       user=user,
                       home_folder=home_folder,
                       client_ssh_key=client_ssh_key,
                       host_ssh_source_key=host_ssh_source_key,
                       )

    def context(self, **kwargs) -> 'Runtime':
        """
        Create a runtime sub-context.

        :param kwargs: sub-context symbols
        :return: runtime sub-context
        """
        return Runtime(self,
                       self.help_generator,
                       self.data,
                       **kwargs)
