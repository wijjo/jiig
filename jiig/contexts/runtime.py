"""
Runner provides data and an API to task call-back functions..
"""

from contextlib import contextmanager
from typing import Text, Iterator, Optional

from jiig.registry import RegisteredContext
from jiig.runtime_tool import RuntimeTool
from jiig.util.alias_catalog import AliasCatalog, open_alias_catalog

from .action import ActionContext
from .context import Context
from .host_context import HostContext


class RuntimeHelpGenerator:
    """Abstract base class implemented by a driver to generate on-demand help output."""
    def generate_help(self, *names: Text, show_hidden: bool = False):
        """
        Provide help output.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        raise NotImplementedError


class Runtime(ActionContext, RegisteredContext):
    """
    Application Runtime class.

    This is the top level context presented to task call-back methods.

    Can also use as a base for registered custom runtime classes.

    Self-registers sub-classes to the context registry.

    The class declaration accepts no keyword arguments.
    """

    def __init__(self,
                 parent: Optional[Context],
                 tool: RuntimeTool,
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
        self.help_generator.generate_help(*names, show_hidden=show_hidden)

    def host_context(self,
                     host: str,
                     host_ip: str = None,
                     user: str = None,
                     home_folder: str = None,
                     client_ssh_key_name: str = None,
                     host_ssh_source_key_name: str = None,
                     client: str = None,
                     ):
        """
        Construct new child HostContext with symbols and methods relevant to host connections.

        To avoid confusion with host-related keywords, **kwargs is not supported
        here. Use a sub-context or call update() to add expansion symbols.

        :param host: host name
        :param host_ip: optional host address (default: queried at runtime)
        :param user: optional user name (default: local client user)
        :param home_folder: optional home folder (default: /home/{user})
        :param client_ssh_key_name: optional client SSH key file base name (default: id_rsa_client)
        :param host_ssh_source_key_name: optional host SSH source key file base name (default: id_rsa_host)
        :param client: optional client name (default: queried at runtime)
        """
        return HostContext(self,
                           host,
                           host_ip=host_ip,
                           user=user,
                           home_folder=home_folder,
                           client_ssh_key_name=client_ssh_key_name,
                           host_ssh_source_key_name=host_ssh_source_key_name,
                           client=client)

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
