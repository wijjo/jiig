"""
Runner provides data and an API to task call-back functions..
"""

import os
from contextlib import contextmanager
from typing import Text, Iterator, TypeVar, ContextManager

from jiig.util.alias_catalog import AliasCatalog, open_alias_catalog
from jiig.driver import Driver, DriverTask
from jiig.util.general import get_client_name
from jiig.util.network import resolve_ip_address

from .host_context import HostContext
from .runtime_context import RuntimeContext
from .runtime_task import RuntimeTask
from .runtime_tool import RuntimeTool

T_runtime = TypeVar('T_runtime', bound='Runtime')


class Runtime(RuntimeContext):
    """Application runtime data and options."""

    def __init__(self,
                 tool: RuntimeTool,
                 root_task: RuntimeTask,
                 driver_root_task: DriverTask,
                 driver: Driver,
                 ):
        """
        Construct root runtime object.

        Passed to Task call-back methods to provide a runtime API and text
        symbol expansion.

        :param tool: tool data
        :param root_task: active root task
        :param driver_root_task: active root task used by driver
        :param driver: active Jiig interface driver
        """
        super().__init__()
        self.tool = tool
        self.root_task = root_task
        self.driver_root_task = driver_root_task
        self.driver = driver
        super().copy_symbols(**self.tool.expansion_symbols)

    def clone(self) -> T_runtime:
        """
        Overridable method to clone a context.

        Subclasses with extended constructors and or extra data members should
        override this method to properly initialize a new instance.

        :return: cloned context instance
        """
        return self.__class__(self.tool, self.root_task, self.driver_root_task, self.driver)

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

    def host_context(self,
                     host: str,
                     host_ip: str = None,
                     user: str = None,
                     home_folder: str = None,
                     client_ssh_key_name: str = None,
                     host_ssh_source_key_name: str = None,
                     client: str = None,
                     ) -> ContextManager[HostContext]:
        """
        Host sub-context context manager.

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
                self.abort(f'Unable to resolve host "{host}" IP address.')
        if client is None:
            client = get_client_name()
        if client_ssh_key_name is None:
            client_ssh_key_name = 'id_rsa_client'
        if host_ssh_source_key_name is None:
            host_ssh_source_key_name = 'id_rsa_host'
        client_ssh_key = os.path.expanduser(f'~/.ssh/{client_ssh_key_name}')
        client_ssh_config = os.path.expanduser('~/.ssh/config')
        client_known_hosts = os.path.expanduser('~/.ssh/known_hosts')
        host_ssh_source_key = os.path.expanduser(f'~/.ssh/{host_ssh_source_key_name}')
        host_ssh_key = os.path.expanduser(f'{home_folder}/.ssh/id_rsa')
        return self.custom_context(
            HostContext,
            host=host,
            host_ip=host_ip,
            user=user,
            home_folder=home_folder,
            host_string=host_string,
            client_ssh_key=client_ssh_key,
            client_ssh_config=client_ssh_config,
            client_known_hosts=client_known_hosts,
            host_ssh_source_key=host_ssh_source_key,
            host_ssh_key=host_ssh_key,
            client=client,
        )
