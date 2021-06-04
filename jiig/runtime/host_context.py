"""
Runtime execution and symbol expansion context.
"""

import os
import subprocess
from typing import Sequence, Union, TypeVar

from jiig.util.general import trim_text_block

from .provisioning_script import ProvisioningScript
from .runtime_context import RuntimeContext

T_provisioning_script = TypeVar('T_provisioning_script', bound=ProvisioningScript)


class HostContext(RuntimeContext):
    """
    Nestable runtime context useful for host SSH connections.

    Provides a suitable API for common host-related actions.

    Holds and uses the following symbols (most have usable defaults):
    * host
    * host_ip
    * user
    * home_folder
    * client_ssh_key_name
    * client_ssh_key
    * host_ssh_source_key_name
    * host_ssh_source_key
    * client
    """

    def remote_command(self,
                       command_string_or_sequence: Union[str, Sequence],
                       predicate: str = None,
                       unchecked: bool = False,
                       messages: dict = None,
                       ) -> subprocess.CompletedProcess:
        with self.script() as script:
            script.action(command_string_or_sequence,
                          predicate=predicate,
                          messages=messages)
            script_text = script.get_script_body()
            escaped_script_text = script_text.replace("'", "\\'")
            with self.sub_context(escaped_script_text=escaped_script_text) as sub_context:
                sub_context.update(
                    ssh_command=(f'''ssh -qt {{x}} '''
                                 f'''bash -c "'{os.linesep}{{escaped_script_text}}{os.linesep}'"'''))
                sub_context.message('command: {ssh_command}')
                if self.options.dry_run:
                    proc = subprocess.CompletedProcess([sub_context.get('ssh_command')], 0)
                else:
                    proc = subprocess.run(sub_context.get('ssh_command'), shell=True)
                    if proc.returncode != 0 and not unchecked:
                        sub_context.abort('Remote command failed.')
                return proc

    def test_ssh_key(self, host: str, user: str, messages: dict = None) -> bool:
        with self.sub_context(host=host, user=user) as sub_context:
            proc = sub_context.run(
                'ssh -o PasswordAuthentication=no {host_string} true 2> /dev/null',
                ignore_dry_run=True,
                unchecked=True,
                messages=messages,
            )
            return proc.returncode == 0

    def setup_connection(self, admin_user: str = None):
        """
        Creates server user and configures SSH key password-less connection.

        :param admin_user: admin user that can create a new user (default: root)
        """

        if admin_user is None:
            admin_user = 'root'

        if self.test_ssh_key(
            host='{host}',
            user='{user}',
            messages={
                'before': 'Checking user {user} SSH connection to host {host}...',
                'success': 'SSH connection is already configured.',
                'failure': 'SSH connection must be configured (multiple password prompts).',
            },
        ):
            return

        with self.script(
            messages={
                'before': '~/.ssh/known_hosts cleanup.',
            },
        ) as client_script:
            client_script.action(
                '''
                cp -f {client_known_hosts} {client_known_hosts}.backup
                egrep -v "^({host}|{host_ip})" {client_known_hosts}.backup > {client_known_hosts} 
                ''',
                predicate='egrep -q "^({host}|{host_ip})" {client_known_hosts}',
                messages={
                    'before': 'Removing host and IP address from {client_known_hosts} as needed...',
                    'skip': 'Host was not found in {client_known_hosts}.',
                },
            )
            client_script.execute_local()

        # Create the remote user as an administrator with sudo permission.
        with self.script(
            messages={
                'before': 'User creation.',
            },
            run_by_root=(admin_user == 'root'),
        ) as server_script:
            server_script.create_user(
                '{user}',
                'sudo',
                messages={
                    'before': 'Creating user {user} as needed...',
                    'skip': 'User {user} already exists.',
                },
            )
            server_script.execute_remote(user=admin_user)

        # Configure the client for key-based connections.
        with self.script(
            messages={
                'before': 'Client SSH configuration for host {host}...',
            },
            unchecked=True,
        ) as client_script:
            client_script.setup_ssh_key('{user}@{client}_{host}', '{client_ssh_key}')
            client_script.install_ssh_key('{host}', '{user}', '{client_ssh_key}')
            client_script.execute_local()

    def configure_ssh_client(self):
        """
        Add a host stanza as needed for convenient connection strings.

        Symbols consumed:
        * host
        * host_ip
        * user
        * client_ssh_key
        """
        with self.sub_context(
            client_ssh_config_stanza=trim_text_block(
                '''
                Host {host}
                    HostName {host_ip}
                    User {user}
                    ForwardAgent yes
                    IdentityFile {client_ssh_key}
                ''').replace(os.linesep, '\\n'),
        ) as sub_context:
            with sub_context.script(
                messages={
                    'before': 'Configuring client SSH for host {host}...',
                },
                unchecked=True,
            ) as script:
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
                script.execute_local()

    def setup_host_ssh_key(self):
        """
        Generate and upload public/private key pair.

        Once a key pair is generated reuse it for all hosts.

        Symbols consumed:
        * host_string
        * home_folder
        * host_ssh_source_key
        """
        with self.script() as script:
            script.setup_ssh_key('{host_string}', '{host_ssh_source_key}')
            script.synchronize_files('{host_ssh_source_key}',
                                     '{host_string}:{home_folder}/.ssh/id_rsa',
                                     skip_existing=True)
            script.synchronize_files('{host_ssh_source_key}.pub',
                                     '{host_string}:{home_folder}/.ssh/id_rsa.pub',
                                     skip_existing=True)
            script.execute_local()
