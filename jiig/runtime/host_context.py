"""
Runtime execution and symbol expansion context.
"""

import os
import subprocess
from typing import Optional, Union, Sequence

from jiig.util.console import abort
from jiig.util.context import Context
from jiig.util.general import trim_text_block, get_client_name
from jiig.util.network import resolve_ip_address
from jiig.util.script import Script

from .provisioning_script import ProvisioningScript
from .runtime_context import RuntimeContext


class HostContext(RuntimeContext):
    """
    Nestable runtime context useful for host SSH connections.

    Provides a suitable API for common host-related actions.

    Holds and uses the following symbols (most have usable defaults):
    * host
    * host_ip
    * host_string
    * client
    * user
    * home_folder
    * client_ssh_key
    * host_ssh_source_key
    """

    def __init__(self,
                 parent: Optional[Context],
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

        Note that **kwargs were not added here to allow specifying more
        expansion symbols. This was to avoid confusion with the special host-
        related keyword arguments. To work around this limitation you can chain
        a call to update() following the constructor call.

        :param parent: parent context for symbol inheritance
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
                abort(f'HostContext is unable to resolve host "{host}" IP address.')
        if client is None:
            client = get_client_name()
        if client_ssh_key_name is None:
            client_ssh_key_name = 'id_rsa_client'
        if host_ssh_source_key_name is None:
            host_ssh_source_key_name = 'id_rsa_host'
        client_ssh_key = os.path.expanduser(f'~/.ssh/{client_ssh_key_name}')
        host_ssh_source_key = os.path.expanduser(f'~/.ssh/{host_ssh_source_key_name}')
        super().__init__(parent,
                         host=host,
                         host_ip=host_ip,
                         host_string=host_string,
                         client=client,
                         user=user,
                         home_folder=home_folder,
                         client_ssh_key=client_ssh_key,
                         host_ssh_source_key=host_ssh_source_key,
                         )

    def test_ssh_key(self,
                     host: str = None,
                     user: str = None,
                     messages: dict = None,
                     ) -> bool:
        """
        Test for successful key-based SSH connection.

        :param host: optional host override (default: {host})
        :param user: optional host user override (default: {user})
        :param messages: optional display messages
        """
        if messages is None:
            messages = {
                'before': 'Checking user {user} SSH connection to host {host}...',
                'success': 'SSH connection is already configured.',
                'failure': 'SSH connection must be configured (multiple password prompts).',
            }
        with RuntimeContext(self,
                            host=host or '{host}',
                            user=user or '{user}',
                            ) as sub_context:
            proc = sub_context.run_script(
                'ssh -o PasswordAuthentication=no {user}@{host} true 2> /dev/null',
                ignore_dry_run=True,
                unchecked=True,
                messages=messages,
            )
            return proc.returncode == 0

    def forget_host(self,
                    host: str = None,
                    host_ip: str = None,
                    messages: dict = None,
                    ):
        """
        Remove host from local ~/.ssh/known_hosts to allow setting up a new connection.

        :param host: optional host override (default: {host})
        :param host_ip: optional host IP override (default: {host_ip})
        :param messages: optional display messages
        """
        if messages is None:
            messages = {
                'before': 'Removing host and IP address from {client_known_hosts} as needed...',
                'skip': 'Host was not found in {client_known_hosts}.',
            }
        with RuntimeContext(self,
                            host=host or '{host}',
                            host_ip=host_ip or '{host_ip}',
                            client_known_hosts='~/.ssh/known_hosts',
                            ) as sub_context:
            script = ProvisioningScript()
            script.action(
                '''
                cp -f {client_known_hosts} {client_known_hosts}.backup
                egrep -v "^({host}|{host_ip})" {client_known_hosts}.backup > {client_known_hosts} 
                ''',
                predicate='egrep -q "^({host}|{host_ip})" {client_known_hosts}',
                messages=messages,
            )
            sub_context.run_script(script)

    def create_user(self,
                    host: str = None,
                    user: str = None,
                    admin_user: str = None,
                    messages: dict = None,
                    ):
        """
        Create user as needed.

        :param host: optional host override (default: {host})
        :param user: optional host user override (default: {user})
        :param admin_user: optional admin user that can create a new user (default: root)
        :param messages: optional display messages
        """
        if messages is None:
            messages = {
                'before': 'Creating user {user} as needed...',
                'skip': 'User {user} already exists.',
            }
        with RuntimeContext(self,
                            host=host or '{host}',
                            user=user or '{user}',
                            admin_user=admin_user or 'root',
                            ) as sub_context:
            # Create the remote user as an administrator with sudo permission.
            create_user_script = ProvisioningScript(
                run_by_root=(sub_context.symbols.admin_user == 'root'))
            create_user_script.create_user('{user}', 'sudo', messages=messages)
            sub_context.run_script(create_user_script, host='{host}', user='{admin_user}')

    def setup_ssh_key(self,
                      host: str = None,
                      user: str = None,
                      label: str = None,
                      client_ssh_key: str = None,
                      ):
        """
        Configure SSH key-based password-less connection.

        :param host: optional host override (default: {host})
        :param user: optional host user override (default: {user})
        :param label: optional label used for generated SSH key (default: {client})
        :param client_ssh_key: optional client SSH key override (default: {client_ssh_key})
        """
        with RuntimeContext(self,
                            host=host or '{host}',
                            user=user or '{user}',
                            label=label or '{client}',
                            client_ssh_key=client_ssh_key or '{client_ssh_key}',
                            ) as sub_context:
            client_ssh_key_script = ProvisioningScript(unchecked=True)
            client_ssh_key_script.setup_ssh_key(key_path='{client_ssh_key}',
                                                label='{user}@{client}_{host}')
            client_ssh_key_script.install_ssh_key('{host}', '{user}', '{client_ssh_key}')
            sub_context.run_script(client_ssh_key_script)

    def configure_ssh_host_settings(self,
                                    host: str = None,
                                    host_ip: str = None,
                                    user: str = None,
                                    client_ssh_key: str = None,
                                    ):
        """
        Add a host stanza as needed for convenient connection strings.

        :param host: optional host override (default: {host})
        :param host_ip: optional host IP override (default: {host_ip})
        :param user: optional host user to test (default: {user})
        :param client_ssh_key: optional client SSH key override (default: {client_ssh_key})
        """
        with RuntimeContext(
            self,
            host=host or '{host}',
            host_ip=host_ip or '{host_ip}',
            user=user or '{user}',
            client_ssh_key=client_ssh_key or '{client_ssh_key}',
            client_ssh_config='~/.ssh/config',
            client_ssh_config_stanza=trim_text_block(
                '''
                Host {host}
                    HostName {host_ip}
                    User {user}
                    ForwardAgent yes
                    IdentityFile {client_ssh_key}
                ''').replace(os.linesep, '\\n'),
        ) as sub_context:
            script = ProvisioningScript(unchecked=True)
            script.action(
                '''
                test -f {client_ssh_config} && echo "" >> {client_ssh_config}
                echo -e "{client_ssh_config_stanza}" >> {client_ssh_config}
                chmod 600 {client_ssh_config}
                ''',
                predicate=r'! egrep -q "^Host\s+{host}" {client_ssh_config}',
                messages={
                    'before': 'Adding SSH configuration stanza (as needed)...',
                    'skip': 'SSH configuration "{client_ssh_config}" already has "{host}" stanza.'
                },
            )
            sub_context.run_script(script)

    def setup_host_ssh_key(self,
                           host_string: str = None,
                           home_folder: str = None,
                           host_ssh_source_key: str = None,
                           ):
        """
        Generate and upload public/private key pair.

        Once a key pair is generated reuse it for all hosts.

        :param host_string: optional host string override (default: {host_string})
        :param home_folder: optional home folder override (default: {home_folder})
        :param host_ssh_source_key: optional host SSH key file override (default: {host_ssh_source_key})
        """
        with RuntimeContext(
            self,
            host_string=host_string or '{host_string}',
            home_folder=home_folder or '{home_folder}',
            host_ssh_source_key=host_ssh_source_key or '{host_ssh_source_key}',
        ) as sub_context:
            script = ProvisioningScript()
            script.setup_ssh_key(key_path='{host_ssh_source_key}',
                                 label='{host_string}')
            script.synchronize_files('{host_ssh_source_key}',
                                     '{host_string}:{home_folder}/.ssh/id_rsa',
                                     skip_existing=True)
            script.synchronize_files('{host_ssh_source_key}.pub',
                                     '{host_string}:{home_folder}/.ssh/id_rsa.pub',
                                     skip_existing=True)
            sub_context.run_script(script)

    def run_remote_script(self,
                          script_text_or_object: Union[str, Sequence[str], Script],
                          host: str = None,
                          user: str = None,
                          messages: dict = None,
                          unchecked: bool = False,
                          ignore_dry_run: bool = False,
                          ) -> subprocess.CompletedProcess:
        """
        Calls ActionContext.run_script() with host and user provided.

        Runs script after saving to a file.

        :param script_text_or_object: script body text from string, list or Script object
        :param host: optional host override (default: {host})
        :param user: optional host user override (default: {user})
        :param messages: optional display messages
        :param unchecked: do not check return code for success
        :param ignore_dry_run: execute even if it is a dry run
        :return: subprocess.CompletedProcess result
        """
        with RuntimeContext(self, host=host or '{host}', user=user or '{user}') as sub_context:
            return sub_context.run_script(script_text_or_object,
                                          host='{host}',
                                          user='{user}',
                                          messages=messages,
                                          unchecked=unchecked,
                                          ignore_dry_run=ignore_dry_run)

    def run_remote_script_code(self,
                               script_text_or_object: Union[str, Sequence[str], Script],
                               host: str = None,
                               user: str = None,
                               messages: dict = None,
                               unchecked: bool = False,
                               ignore_dry_run: bool = False,
                               ) -> subprocess.CompletedProcess:
        """
        Calls ActionContext.run_script_code() with host and user provided.

        Runs code without saving to file.

        :param script_text_or_object: script body text from string, list or Script object
        :param host: optional host override (default: {host})
        :param user: optional host user override (default: {user})
        :param messages: optional display messages
        :param unchecked: do not check return code for success
        :param ignore_dry_run: execute even if it is a dry run
        :return: subprocess.CompletedProcess result
        """
        with RuntimeContext(self, host=host or '{host}', user=user or '{user}') as sub_context:
            return sub_context.run_script_code(script_text_or_object,
                                               host='{host}',
                                               user='{user}',
                                               messages=messages,
                                               unchecked=unchecked,
                                               ignore_dry_run=ignore_dry_run)
