"""
Scripter for provisioning actions.
"""

import os
from typing import List

from ..util.general import plural, trim_text_block
from ..util.git import repo_name_from_url
from ..util.process import shell_quote_path
from ..util.script import Script

from .filesystem import create_parent_folder, create_folder, create_symlink, deploy_files


def create_user(script: Script,
                user: str,
                *groups: str,
                messages: dict = None,
                ):
    """
    Add user creation to script.

    :param script: script to receive actions
    :param user: user to create
    :param groups: user assigned groups
    :param messages: output messages (defaults provided)
    """
    if messages is None:
        messages = {
            'before': f'Creating user (as needed): {user}',
            'skip': f'User "{user}" already exists.',
        }
    with script.block(predicate=f'! grep -q ^{user}: /etc/passwd', messages=messages):
        script.action(
            [
                script.wrap_command(f'adduser {user}', need_root=True)
            ] + [
                script.wrap_command(f'usermod -aG %s {user}' % group, need_root=True)
                for group in groups
            ],
            messages=messages,
        )


def create_ssh_key(script: Script,
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


def install_ssh_key_on_host(script: Script,
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


def test_git_connection(script: Script, key_path: str = None):
    """
    Test Git connection and display public key if it fails.

    :param script: script to receive actions
    :param key_path: base SSH key file path
    """
    key_path = key_path or '~/.ssh/id_rsa'
    with script.block(
        predicate='! {{ ssh -T git@github.com || [ $? -eq 1 ]; }}',
        messages={
            'before': 'Checking that Git connection works...',
            'skip': 'Git connection was successful.',
        },
    ):
        script.action(
            f'''
            cat {key_path}.pub
            echo "Add the above key to GitHub (https://github.com/settings/keys)."
            read -p "Press Enter to continue:"
            ''',
        )


def clone_git_repository(script: Script,
                         repo_url: str,
                         repo_folder: str,
                         flat: bool = False,
                         ):
    """
    Clone local Git repository.

    :param script: script to receive actions
    :param repo_url: repository URL
    :param repo_folder: local repository folder
    :param flat: omit --recurse-submodules flag if True
    """
    option_string = ' --recurse-submodules' if not flat else ''
    create_parent_folder(script, repo_folder)
    quoted_repo_folder = shell_quote_path(repo_folder)
    with script.block(
        predicate=f'[[ ! -d {quoted_repo_folder} ]]',
        messages={
            'before': f'Cloning Git repository folder (as needed): {repo_folder}',
            'skip': f'Local repository folder {repo_folder} exists.',
        },
    ):
        script.action(f'git clone{option_string} {repo_url} {quoted_repo_folder}')


def configure_git(script: Script,
                  host_ssh_key: str = None,
                  config_repo_url: str = None,
                  config_folder: str = None,
                  config_source: str = None,
                  ):
    """
    Install and configure Git for user.

    Optionally clone configuration repository and symlink to ~/.gitconfig
    source file.

    :param script: script to receive actions
    :param host_ssh_key: SSH key path (default: ~/.ssh/id_rsa)
    :param config_repo_url: optional configuration repository URL
    :param config_folder: optional local configuration repository folder
    :param config_source: optional path to ~/.gitconfig symlink source file
    """
    apt_install(script, '/usr/bin/git', 'git')
    create_ssh_key(script, key_path=host_ssh_key)
    test_git_connection(script, key_path=host_ssh_key)
    if config_repo_url:
        if not config_folder:
            config_folder = f'~/{repo_name_from_url(config_repo_url)}'
        clone_git_repository(script, config_repo_url, config_folder)
    if config_source:
        create_symlink(script, config_source, '~/.gitconfig')


def install_network_tools(script: Script):
    """
    Install curl and wget.

    :param script: script to receive actions
    """
    apt_install(script, '/usr/bin/curl', 'curl')
    apt_install(script, '/usr/bin/wget', 'wget')
    apt_install(script, '/usr/bin/rsync', 'rsync')


def apt_install(script: Script,
                executable: str,
                *packages: str,
                messages: dict = None,
                ):
    """
    Install package(s) using apt.

    Override Script method to provide default messages.

    :param script: script to receive actions
    :param executable: presence of this executable indicates the install is unnecessary
    :param packages: package(s) to install
    :param messages: messages to display
    """
    primary_package = packages[0]
    packages_string = ' '.join(packages)
    package_word = plural('package', packages)
    if messages is None:
        messages = {
            'before': f'Installing Apt {package_word}'
                      f' (if {executable} is missing): {packages_string}',
            'skip': f'Package {primary_package} is already installed.',
        }
    with script.block(
        predicate=f'! command -v {executable} > /dev/null',
        messages=messages,
    ):
        script.action(
            script.wrap_command(f'apt install -y {packages_string}', need_root=True),
            messages=messages,
        )


def change_user_shell(script: Script,
                      user: str,
                      shell: str,
                      messages: dict = None,
                      ):
    """
    Add user shell changing to script.

    :param script: script to receive actions
    :param user: user name
    :param shell: shell to assign
    :param messages: output messages
    """
    if messages is None:
        messages = {
            'before': f'Changing shell for user "{user}" (as needed): {shell}',
            'skip': f'Shell is already {shell}.'
        }
    with script.block(
        predicate=f'[[ $SHELL != {shell} ]]',
        messages=messages,
    ):
        script.action(
            script.wrap_command(f'chsh -s {shell} {user}', need_root=True),
            messages=messages,
        )


def configure_bash(script: Script,
                   user: str,
                   rc_source: str,
                   default_shell: bool = False,
                   ):
    """
    Configure bash for user.

    :param script: script to receive actions
    :param user: user name
    :param rc_source: ~/.bashrc source path
    :param default_shell: make Bash the user shell if True
    """
    bashrc_command = f'test -f {rc_source} && source {rc_source}'
    with script.block(
        predicate=f'! grep -q {rc_source} ~/.bashrc',
        messages={
            'before': 'Hooking up ~/.bashrc as needed...',
            'skip': '~/.bashrc is already hooked up.',
        },
    ):
        script.action(f"echo -e '\\n{bashrc_command}' >> ~/.bashrc")
    if default_shell:
        change_user_shell(script, user, '/bin/bash')


def install_and_configure_zsh(script: Script,
                              user: str,
                              rc_source: str = None,
                              login_source: str = None,
                              profile_source: str = None,
                              env_source: str = None,
                              theme_source: str = None,
                              theme_target: str = None,
                              default_shell: bool = False,
                              oh_my_zsh: bool = False,
                              ):
    """
    Install and configure ZSH for user.

    Caveats:
    * Works with a set of user-provided configuration files, rather than
      trying to edit existing ones.
    * Configuration files are symlinked to the user home folder.
    * Oh-my-zsh setup assumes the ~/.zshrc source file is pre-configured for
      oh-my-zsh. It undoes the oh-my-zsh ~/.zshrc changes.

    :param script: script to receive actions
    :param user: user name
    :param rc_source: ~/.zshrc source path
    :param login_source: ~/.zlogin source path
    :param profile_source: ~/.zprofile source path
    :param env_source:  ~/.zshenv source path
    :param theme_source: ZSH theme source path
    :param theme_target: ZSH theme target path
    :param default_shell: change the user's default shell if True
    :param oh_my_zsh: install oh-my-zsh if True
    """
    apt_install(script, '/usr/bin/zsh', 'zsh', 'zsh-doc')
    create_symlink(script, rc_source, '~/.zshrc')
    if login_source:
        create_symlink(script, login_source, '~/.zlogin')
    if profile_source:
        create_symlink(script, profile_source, '~/.zprofile')
    if env_source:
        create_symlink(script, env_source, '~/.zshenv')
    if theme_source:
        if theme_source and not theme_target:
            theme_target = f'~/.{os.path.basename(theme_source)}'
        create_symlink(script, theme_source, theme_target)
    if default_shell:
        change_user_shell(script, user, '/usr/bin/zsh')
    if oh_my_zsh:
        with script.block(
            predicate='[[ ! -e ~/.oh-my-zsh ]]',
            messages={
                'before': 'Installing oh-my-zsh as needed...',
                'skip': '~/.oh-my-zsh exists, assuming oh-my-zsh is already installed.',
            },
        ):
            script.action(
                '''
                pushd /tmp > /dev/null
                wget https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh
                popd > /dev/null
                echo "Running oh-my-zsh installer..."
                sh /tmp/install.sh --unattended > /tmp/oh-my-zsh-install.log
                if [[ -f ~/.zshrc.pre-oh-my-zsh ]]; then
                    rm -f ~/.zshrc
                    mv ~/.zshrc.pre-oh-my-zsh ~/.zshrc
                fi
                ''',
            )


def install_and_configure_neovim(script: Script,
                                 rc_source: str,
                                 install_plugins: bool = False,
                                 ):
    """
    Install and configure NeoVim for user.

    :param script: script to receive actions
    :param rc_source: ~/.config/nvim/init.vim source path
    :param install_plugins: install plugins if True
    """
    rc_target = '~/.config/nvim/init.vim'
    vundle_url = 'https://github.com/VundleVim/Vundle.vim.git'
    vundle_path = '~/.local/share/nvim/bundle/Vundle.vim'
    apt_install(script, '/usr/bin/nvim', 'neovim')
    create_folder(script, '~/.config/nvim')
    create_folder(script, '~/.local/share/nvim')
    create_symlink(script, rc_source, rc_target)
    if install_plugins:
        with script.block(
            predicate=f'[[ ! -d {vundle_path} ]]',
            messages={
                'before': 'Installing NeoVim plugins as needed...',
                'skip': 'NeoVim plugin folder already exists.',
            },
        ):
            script.action(
                f'''
                git clone {vundle_url} {vundle_path}
                nvim +PluginInstall +qall
                ''',
            )


def configure_readline(script: Script,
                       bell_style: str = None,
                       completion_ignore_case: bool = False,
                       horizontal_scroll_mode: bool = False,
                       ):
    """
    Create a custom ~/.inputrc for shell input handling via readline.

    Note that {rc_source} is copied, not symlinked, when specified.
    Additional options are applied to ~/.inputrc.

    Only a limited set of options are supported.

    See `man readline` for more information.

    :param script: script to receive actions
    :param bell_style: e.g. "none", "visible", or "audible" (default: none)
    :param completion_ignore_case: case-insensitive completion if True (default: False)
    :param horizontal_scroll_mode: single line horizontal scrolling (default: False)
    """
    bell_style = bell_style or 'none'
    completion_ignore_case = 'on' if completion_ignore_case else 'off'
    horizontal_scroll_mode = 'on' if horizontal_scroll_mode else 'off'
    body = os.linesep.join(
        [
            f'set bell-style {bell_style}',
            f'set completion-ignore-case {completion_ignore_case}',
            f'set horizontal-scroll-mode {horizontal_scroll_mode}',
        ],
    )
    with script.block(
        predicate='[[ ! -e ~/.inputrc ]]',
        messages={
            'before': 'Generating ~/.inputrc...',
            'skip': '~/.inputrc already exists.'
        },
    ):
        script.action(f'echo "{body}" > ~/.inputrc')


def install_and_configure_pyenv(script: Script, enable_betas: bool = False):
    """
    Install prerequisites, install pyenv, and configure shell to use it.

    Caveats:
    * Does nothing if ~/.pyenv exists.
    * Expect that ~/.bashrc, ~/.zshrc, etc. will already have recommended
      pyenv initialization environment setup and initialization.
    * Currently it can only choose either the latest stable or beta release, not
      from any earlier or other releases.

    See https://github.com/pyenv/pyenv.

    :param script: script to receive actions
    :param enable_betas: enable beta releases if True
    """
    # noinspection SpellCheckingInspection
    apt_install(script, 'make', 'build-essential', 'libssl-dev', 'zlib1g-dev',
                'libbz2-dev', 'libreadline-dev', 'libsqlite3-dev', 'wget',
                'curl', 'llvm', 'libncursesw5-dev', 'xz-utils', 'tk-dev',
                'libxml2-dev', 'libxmlsec1-dev', 'libffi-dev', 'liblzma-dev')
    with script.block(
        predicate='[[ ! -e ~/.pyenv ]]',
        messages={
            'before': 'Cloning ~/.pyenv...',
            'skip': '~/.pyenv already exists.'
        },
    ):
        clone_git_repository(script, 'https://github.com/pyenv/pyenv.git', '~/.pyenv')
        with script.block(location='~/.pyenv'):
            script.action([
                'src/configure',
                'make -C src',
            ])
        beta_characters = 'a-z' if enable_betas else ''
        script.action([
            'export PATH="~/.pyenv/bin:$PATH"',
            (fr"_version=$("
                r"pyenv install --list"
                fr" | sed -n 's/^ *\([0-9]\+\.[0-9]\+\.[0-9{beta_characters}]*\) *$/\1/p'"
                r" | tail -1"
                r")"),
            'test -n "$_version"',
            'pyenv install $_version',
            'pyenv global $_version',
            'eval "$(pyenv init --path)"',
        ])


def test_ssh_key_connection(script: Script,
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


def forget_ssh_host(script: Script,
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


def configure_ssh_host_settings(script: Script,
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


def create_and_deploy_ssh_key(script: Script,
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
    create_ssh_key(script, key_path=host_ssh_source_key, label=host_string)
    remote_private_path = f'{host_string}:{home_folder}/.ssh/id_rsa'
    deploy_files(script, host_ssh_source_key, remote_private_path,
                 skip_existing=True)
    public_path = f'{host_ssh_source_key}.pub'
    remote_public_path = f'{host_string}:{home_folder}/.ssh/id_rsa.pub'
    deploy_files(script, public_path, remote_public_path,
                 skip_existing=True)
