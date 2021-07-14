"""
Runner provides data and an API to task call-back functions..
"""

import os
from contextlib import contextmanager
from typing import Text, Iterator, Optional, Callable, List

from ..contexts.action import ActionContext
from ..contexts.context import Context
from ..util.alias_catalog import AliasCatalog, open_alias_catalog
from ..util.general import get_client_name
from ..util.network import resolve_ip_address

from .context_registry import SelfRegisteringContextBase
from .tool import Tool


class RuntimeHelpGenerator:
    """Abstract base class implemented by a driver to generate on-demand help output."""
    def generate_help(self, *names: Text, show_hidden: bool = False):
        """
        Provide help output.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        raise NotImplementedError


class Runtime(ActionContext, SelfRegisteringContextBase):
    """
    Application Runtime class.

    This is the top level context presented to task call-back methods.

    Can also use as a base for registered custom runtime classes.

    Self-registers sub-classes to the context registry.

    The class declaration accepts no keyword arguments.
    """

    def __init__(self,
                 parent: Optional[Context],
                 tool: Tool,
                 help_generator: RuntimeHelpGenerator,
                 data: object,
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
        :param kwargs: initial symbols
        """
        self.tool = tool
        self.help_generator = help_generator
        self.data = data
        self.when_done_callables: List[Callable] = []
        super().__init__(
            parent,
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
            tool_name=tool.tool_name,
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
        with open_alias_catalog(self.tool.tool_name, self.tool.aliases_path) as catalog:
            yield catalog

    def provide_help(self, *names: Text, show_hidden: bool = False):
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
                       self.tool,
                       self.help_generator,
                       self.data,
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
                       self.tool,
                       self.help_generator,
                       self.data,
                       **kwargs)

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
