import os
from contextlib import contextmanager
from typing import Optional, ContextManager

from .messages import Messages
from .provisioning_script import ProvisioningScript
from .scripter import Scripter
from .utility import get_client_name, trim_text_block


class Provisioner(Scripter):
    """
    Somewhat flexible host provisioner.

    Things that are assumed or hard-coded:
    * User has a configuration repository with well-known configuration file names.
    * SSH key file names are based on project and server user names.
    * User gets created as an administrator with sudo privileges.
    * ~/.ssh/config gets a stanza for the host for easy login.

    Symbols initialized:
    * project
    * user
    * client
    """

    def __init__(self,
                 debug: bool = False,
                 dry_run: bool = False,
                 pause: bool = False,
                 **kwargs,
                 ):
        super().__init__(debug=debug, dry_run=dry_run, pause=pause, **kwargs)
        # Provide client name symbol for free.
        if 'client' not in kwargs:
            self.update(client=get_client_name())

    @contextmanager
    def host_provisioner(self,
                         host: str,
                         host_ip: Optional[str],
                         ) -> ContextManager['Provisioner']:
        if host_ip:
            host_ip = host_ip
        else:
            host_ip = self.get_ip_address(host)
        with self.sub_scripter(
            host=host,
            host_ip=host_ip,
            client_ssh_config_stanza=trim_text_block('''
            Host {host}
                HostName {host_ip}
                User {user}
                ForwardAgent yes
                IdentityFile {client_ssh_key}
            ''').replace(os.linesep, '\\n'),
        ) as host_provisioner:
            yield host_provisioner

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
            messages=Messages(
                heading='Checking user {user} SSH connection to host {host}...',
                success='SSH connection is already configured.',
                failure='SSH connection must be configured (multiple password prompts).',
            ),
        ):
            return

        with self.start_script(heading='~/.ssh/known_hosts cleanup.') as client_script:
            client_script.action(
                '''
                cp -f {client_known_hosts} {client_known_hosts}.backup
                egrep -v "^({host}|{host_ip})" {client_known_hosts}.backup > {client_known_hosts} 
                ''',
                predicate='egrep -q "^({host}|{host_ip})" {client_known_hosts}',
                messages=Messages(
                    heading='Removing host and IP address from {client_known_hosts} as needed...',
                    skip='Host was not found in {client_known_hosts}.',
                ),
            )
            client_script.execute()

        # Create the remote user as an administrator with sudo permission.
        with self.start_script(heading='User creation.',
                               run_as_root=(admin_user == 'root'),
                               ) as server_script:
            server_script.create_user(
                '{user}',
                'sudo',
                messages=Messages(
                    heading='Creating user {user} as needed...',
                    skip='User {user} already exists.',
                ),
            )
            server_script.execute(host='{host}', user=admin_user, )

        # Configure the client for key-based connections.
        with self.start_script(
            heading='Client SSH configuration for host {host}...',
            unchecked=True,
        ) as client_script:
            client_script.action(
                '''
                ssh-keygen -C {user}@{client}_{host} -f {client_ssh_key}
                ''',
                predicate='[[ ! -f {client_ssh_key} ]]',
                messages=Messages(
                    heading='Generating client public/private keys as needed...',
                    skip='Key file {client_ssh_key} exists.',
                ),
            )
            client_script.action(
                '''
                ssh-copy-id -i {client_ssh_key}.pub {user}@{host}
                ''',
                messages=Messages(
                    heading='Copying key to the server...',
                )
            )
            client_script.execute()

    def setup_ssh_client_configuration(self):
        """Add a host stanza as needed for convenient connection strings."""
        with self.start_script(
            heading='Configuring client SSH for host {host}...',
            unchecked=True,
        ) as script:
            script.action(
                '''
                test -f {client_ssh_config} && echo "" >> {client_ssh_config}
                echo -e "{client_ssh_config_stanza}" >> {client_ssh_config}
                chmod 600 {client_ssh_config}
                ''',
                predicate=r'! egrep -q "^Host\s+{host}" {client_ssh_config}',
                messages=Messages(
                    heading='Adding SSH configuration stanza (as needed)...',
                    skip='SSH configuration "{client_ssh_config}" already has "{host}" stanza.'
                ),
            )
            script.execute()

    @contextmanager
    def start_provisioning_script(self,
                                  heading: str = None,
                                  unchecked: bool = False,
                                  run_as_root: bool = False,
                                  ) -> ContextManager[ProvisioningScript]:
        with self.start_script(heading=heading,
                               unchecked=unchecked,
                               run_as_root=run_as_root,
                               script_class=ProvisioningScript,
                               ) as script:
            yield script
