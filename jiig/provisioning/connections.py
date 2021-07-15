"""
All-in-one scripter and runner to check and provision a host connection.
"""

import os
from typing import List

from jiig import Script, ActionContext
from jiig.util.general import trim_text_block

from .files import script_file_deployment
from .packages import script_apt_package_installation
from .users import script_user_creation


def script_ssh_key_creation(script: Script,
                            key_path: str = None,
                            label: str = None,
                            messages: dict = None,
                            ):
    """
    Generate SSH key pair as needed.

    :param script: script to receive actions
    :param key_path: optional key file path (default: ~/.ssh/id_rsa
    :param label: optional label (comment) for generated key (default: no label/comment)
    :param messages: output messages (defaults provided)
    """
    option_parts: List[str] = []
    if label:
        option_parts.append(f'-C {label}')
    if key_path:
        option_parts.append(f'-f {key_path}')
    else:
        key_path = '~/.ssh/id_rsa'
    option_string = f' {" ".join(option_parts)}' if option_parts else ''
    if messages is None:
        messages = {
            'before': f'Generating keys (as needed): {key_path}',
            'skip': f'Key file {key_path} exists.',
        }
    with script.block(
        predicate=f'[[ ! -f {key_path} ]]',
        messages=messages,
    ):
        script.action(
            f'ssh-keygen{option_string}',
            messages=messages,
        )


def script_ssh_key_deployment(script: Script,
                              host_string: str,
                              key_path: str,
                              messages: dict = None,
                              ):
    """
    Install SSH public key on host.

    :param script: script to receive actions
    :param host_string: host connection string
    :param key_path: key file base path
    :param messages: output messages (defaults provided)
    """
    if messages is None:
        messages = {
            'before': f'Copying SSH key to {host_string}: {key_path}',
        }
    script.action(
        f'ssh-copy-id -i {key_path}.pub {host_string}',
        messages=messages,
    )


def script_network_tool_installation(script: Script):
    """
    Install curl and wget.

    :param script: script to receive actions
    """
    script_apt_package_installation(script, '/usr/bin/curl', 'curl')
    script_apt_package_installation(script, '/usr/bin/wget', 'wget')
    script_apt_package_installation(script, '/usr/bin/rsync', 'rsync')


def script_ssh_key_based_connection_test(script: Script,
                                         host: str,
                                         user: str,
                                         messages: dict = None,
                                         ):
    """
    Test for successful key-based SSH connection.

    :param script: script to receive actions
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
    script.action(f'ssh -o PasswordAuthentication=no {user}@{host} true 2> /dev/null',
                  messages=messages)


def script_ssh_known_host_removal(script: Script,
                                  host: str,
                                  host_ip: str,
                                  messages: dict = None,
                                  ):
    """
    Remove host from local ~/.ssh/known_hosts to allow setting up a new connection.

    :param script: script to receive actions
    :param host: host name
    :param host_ip: host IP address
    :param messages: optional display messages
    """
    if messages is None:
        messages = {
            'before': 'Removing host and IP address from ~/.ssh/known_hosts as needed...',
            'skip': f'Host ({host} or {host_ip}) was not found in ~/.ssh/known_hosts.',
        }
    with script.block(predicate=f'egrep -q "^({host}|{host_ip})" ~/.ssh/known_hosts',
                      messages=messages):
        script.action(
            f'''
            cp -f ~/.ssh/known_hosts ~/.ssh/known_hosts.backup
            egrep -v "^({host}|{host_ip})" ~/.ssh/known_hosts.backup > ~/.ssh/known_hosts
            ''',
            messages=messages,
        )


def script_ssh_host_connection_configuration(script: Script,
                                             host: str,
                                             host_ip: str,
                                             user: str,
                                             client_ssh_key: str,
                                             ):
    """
    Add a host stanza as needed for convenient connection strings.

    :param script: script to receive actions
    :param host: host name
    :param host_ip: host IP address
    :param user: host user
    :param client_ssh_key: client SSH key path
    """
    client_ssh_config = '~/.ssh/config'
    client_ssh_config_stanza = trim_text_block(
            f'''
            Host {host}
                HostName {host_ip}
                User {user}
                ForwardAgent yes
                IdentityFile {client_ssh_key}
            ''').replace(os.linesep, '\\n')
    with script.block(
        predicate=rf'! egrep -q "^Host\s+{host}" {client_ssh_config}',
        messages={
            'before': 'Adding SSH configuration stanza (as needed)...',
            'skip': f'SSH configuration "{client_ssh_config}" already has "{host}" stanza.'
        },
    ):
        script.action(
            f'''
            test -f {client_ssh_config} && echo "" >> {client_ssh_config}
            echo -e "{client_ssh_config_stanza}" >> {client_ssh_config}
            chmod 600 {client_ssh_config}
            ''',
        )


def script_ssh_key_creation_and_deployment(script: Script,
                                           host_string: str,
                                           home_folder: str,
                                           host_ssh_source_key: str,
                                           ):
    """
    Generate and upload public/private key pair.

    Once a key pair is generated reuse it for all hosts.

    :param script: script to receive actions
    :param host_string: host connection string
    :param home_folder: home folder path
    :param host_ssh_source_key: host SSH key path
    """
    script_ssh_key_creation(script, key_path=host_ssh_source_key, label=host_string)
    remote_private_path = f'{host_string}:{home_folder}/.ssh/id_rsa'
    script_file_deployment(script, host_ssh_source_key, remote_private_path,
                           skip_existing=True)
    public_path = f'{host_ssh_source_key}.pub'
    remote_public_path = f'{host_string}:{home_folder}/.ssh/id_rsa.pub'
    script_file_deployment(script, public_path, remote_public_path,
                           skip_existing=True)


def provision_key_based_ssh_connection(context: ActionContext,
                                       host: str,
                                       host_ip: str,
                                       user: str,
                                       client_ssh_key: str = None,
                                       admin_user: str = None,
                                       key_label: str = None,
                                       ):
    """
    All-in-one function assures a key-based SSH connection is available.

    Tests whether or not a key-based connection already works.

    If not, it performs the following steps, as needed:
      - Forget previous remembered instances of the host.
      - Create a missing user.
      - Generate SSH key pair.
      - Configure host connection stanza in ~/.ssh/config.

    :param context: context used for script execution.
    :param host: host name
    :param host_ip: host IP address
    :param user: user name on host
    :param client_ssh_key: ssh private key path (default is ~/.ssh/id_rsa)
    :param admin_user: admin user that can create a user, if missing (default is root)
    :param key_label: label for generated ssh key (default is user@host)
    """
    # Local: Test for functioning SSH key-based connection or configure if necessary.
    test_ssh_script = Script()
    script_ssh_key_based_connection_test(test_ssh_script, host, user)
    proc = context.run.script(test_ssh_script, ignore_dry_run=True, unchecked=True)
    if proc.returncode == 0:
        # We're good, key-based SSH connection works!.
        return

    if not admin_user:
        admin_user = 'root'
    if not key_label:
        key_label = f'{user}@{host}'
    if not client_ssh_key:
        client_ssh_key = '~/.ssh/id_rsa'
    host_string = f'{user}@{host}'

    # Local: Remove host from known hosts to avoid man-in-the-middle attack errors.
    forget_host_script = Script()
    script_ssh_known_host_removal(forget_host_script, host, host_ip)
    context.run.script(forget_host_script)

    # Remote: Create user as needed.
    create_user_script = Script()
    script_user_creation(create_user_script, user, 'sudo')
    context.run.script(create_user_script, host=host, user=admin_user)

    # Local: Set up SSH key pair as needed.
    client_ssh_key_script = Script(unchecked=True)
    script_ssh_key_creation(client_ssh_key_script,
                            key_path=client_ssh_key,
                            label=key_label)
    script_ssh_key_deployment(client_ssh_key_script,
                              host_string=host_string,
                              key_path=client_ssh_key)
    context.run.script(client_ssh_key_script)

    # Local: Configure ~/.ssh/config host stanza as needed.
    host_ssh_script = Script(unchecked=True)
    script_ssh_host_connection_configuration(host_ssh_script,
                                             host,
                                             host_ip,
                                             user,
                                             client_ssh_key)
    context.run.script(host_ssh_script)
