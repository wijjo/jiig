"""
Scripter provisioning script.
"""

import os
from typing import List, Sequence, Union

from jiig.util.general import make_list
from jiig.util.script import Script
from jiig.util.process import shell_quote_arg

from .options import Options


class ProvisioningScript(Script):
    """Script that can perform local and remote provisioning tasks."""

    def create_user(self, user: str, *groups: str, messages: dict = None):
        """
        Add user creation to script.

        :param user: user to create
        :param groups: user assigned groups
        :param messages: output messages
        """
        with self.sub_script(user=user) as sub_script:
            sub_script.add_block(
                [
                    self._wrap_command('adduser {user}', need_root=True)
                ] + [
                    self._wrap_command('usermod -aG %s {user}' % group, need_root=True)
                    for group in groups
                ],
                predicate='! grep -q ^{user}: /etc/passwd',
                messages=messages,
            )

    def create_folder(self, folder: str, need_root: bool = False, messages: dict = None):
        """
        Add folder creation to script.

        :param folder: folder to create
        :param need_root: requires root to create it successfully
        :param messages: output messages
        """
        with self.sub_script(folder=folder) as sub_script:
            sub_script.add_block(
                self._wrap_command('mkdir -p {folder}', need_root=need_root),
                predicate='[[ ! -d {folder} ]]',
                messages=messages,
            )

    def delete_folder(self, folder: str, need_root: bool = False, messages: dict = None):
        """
        Add folder deletion to script.

        :param folder: folder to delete
        :param need_root: requires root to delete it successfully
        :param messages: output messages
        """
        with self.sub_script(
            folder=folder,
            redirect=' 2> /dev/null' if not Options.debug else '',
        ) as sub_script:
            sub_script.add_block(
                self._wrap_command('rm -rf {folder}{redirect}', need_root=need_root),
                predicate='[[ -d {folder} ]]',
                messages=messages,
            )

    def symlink(self, source: str, target: str, messages: dict = None):
        """
        Add symbolic link creation to script.

        :param source: source path
        :param target: target symlink path
        :param messages: output messages
        """
        with self.sub_script(source=source, target=target) as sub_script:
            sub_script.add_block(
                '''
                ln -s {source} {target}
                ''',
                predicate='[[ ! -e {target} ]]',
                messages=messages,
            )

    def setup_ssh_key(self, label: str, key_path: str):
        """
        Generate SSH key pair as needed.

        :param label: label (comment) for generated key
        :param key_path: key file path
        """
        with self.sub_script(label=label, key_path=key_path) as sub_script:
            sub_script.action(
                '''
                ssh-keygen -C {label} -f {key_path}
                ''',
                predicate='[[ ! -f {key_path} ]]',
                messages={
                    'before': 'Generating {key_path} keys as needed...',
                    'skip': 'Key file {key_path} exists.',
                },
            )

    def install_ssh_key(self, host: str, user: str, key_path: str):
        """
        Install SSH public key on host.

        :param host: host name or address
        :param user: user name
        :param key_path: key file base path
        """
        with self.sub_script(host=host, user=user, key_path=key_path) as sub_script:
            sub_script.action(
                '''
                ssh-copy-id -i {key_path}.pub {user}@{host}
                ''',
                messages={
                    'before': 'Copying key {key_path} to the server...',
                },
            )

    def setup_git(self):
        """
        Install and configure Git for user.

        Symbols consumed:
        * host_ssh_key
        * config_folder
        * gitconfig_source
        """

        self.apt_install('/usr/bin/git', 'git')

        self.action(
            '''
            ssh-keygen -f {host_ssh_key}
            ''',
            predicate='[[ ! -f {host_ssh_key} ]]',
            messages={
                'before': 'Making sure SSH key {host_ssh_key} is available...',
                'skip': 'SSH keys exist.',
            },
        )

        self.action(
            '''
            cat {host_ssh_key}.pub
            echo "Add the above key to GitHub (https://github.com/settings/keys)."
            read -p "Press Enter to continue:"
            ''',
            predicate='! {{ ssh -T git@github.com || [ $? -eq 1 ]; }}',
            messages={
                'before': 'Checking that Git connection works...',
                'skip': 'Git connection was successful.',
            },
        )

        parent_folder = os.path.dirname(self.context.format('{config_folder}'))
        self.create_folder(
            parent_folder,
            messages={
                'before': f'Making sure repository parent folder {parent_folder} exists...',
                'skip': f'Repository parent folder {parent_folder} exists.',
            },
        )

        self.action(
            '''
            git clone --recurse-submodules {config_repo_url}
            ''',
            predicate='[[ ! -d {config_folder} ]]',
            location=parent_folder,
            messages={
                'before': 'Cloning configuration folder {config_folder} as needed...',
                'skip': 'Configuration folder {config_folder} exists.',
            },
        )

        self.symlink(
            '{gitconfig_source}', '~/.gitconfig',
            messages={
                'before': 'Adding ~/.gitconfig symlink if missing...',
                'skip': '~/.gitconfig already exists.',
            },
        )

    def setup_network_tools(self):
        """
        Install curl and wget.

        No symbols consumed.
        """
        self.apt_install('/usr/bin/curl', 'curl')
        self.apt_install('/usr/bin/wget', 'wget')
        self.apt_install('/usr/bin/rsync', 'rsync')

    def apt_install(self,
                    executable: str,
                    *packages: str,
                    messages: dict = None,
                    ):
        """
        Install package(s) using apt.

        Override Script method to provide default messages.

        :param executable: presence of this executable indicates the install is unnecessary
        :param packages: package(s) to install
        :param messages: messages to display
        """
        with self.sub_script(executable=executable,
                             primary_package=packages[0],
                             packages=' '.join(packages),
                             ) as sub_script:
            if messages is None:
                messages = {
                    'before': 'Installing {primary_package} as needed with apt...',
                    'skip': 'Package {primary_package} is already installed.',
                }
            sub_script.add_block(
                self._wrap_command('apt install -y {packages}', need_root=True),
                predicate='! command -v {executable} > /dev/null',
                messages=messages,
            )

    def change_shell(self, user: str, shell: str, messages: dict = None):
        """
        Add user shell changing to script.

        :param user: user name
        :param shell: shell to assign
        :param messages: output messages
        :return:
        """
        with self.sub_script(user=user, shell=shell) as sub_script:
            sub_script.add_block(
                self._wrap_command('chsh -s {shell} {user}', need_root=True),
                predicate='[[ $SHELL != {shell} ]]',
                messages=messages,
            )

    def setup_bash(self, default_shell: bool = False):
        """
        Configure bash for user.

        Configuration repository must be present.

        Symbols consumed:
        * config_folder
        * bashrc_source

        :param default_shell: make Bash the user shell if True
        """

        with self.sub_script(
            bashrc_command='test -f {bashrc_source} && source {bashrc_source}',
        ) as sub_script:
            sub_script.action(
                '''
                echo -e '\\n{bashrc_command}' >> ~/.bashrc
                ''',
                predicate='! grep -q {config_folder} ~/.bashrc',
                messages={
                    'before': 'Hooking up ~/.bashrc as needed...',
                    'skip': '~/.bashrc is already hooked up.',
                },
            )

        if default_shell:
            self.change_shell(
                '{user}', '/bin/bash',
                messages={
                    'before': 'Changing user shell to Bash as needed...',
                    'skip': 'Shell is already Bash.',
                },
            )

    def setup_zsh(self, default_shell: bool = False):
        """
        Install and configure ZSH for user.

        Configuration repository must be present.

        Symbols consumed:
        * zshrc_source
        * zlogin_source
        * zprofile_source
        * zshenv_source
        * zsh_theme_source
        * zsh_theme_target

        :param default_shell: change the user's default shell if True
        """
        self.apt_install('/usr/bin/zsh', 'zsh', 'zsh-doc')

        self.symlink(
            '{zshrc_source}',
            '~/.zshrc',
            messages={
                'before': 'Adding ~/.zshrc symlink if missing...',
                'skip': '~/.zshrc already exists.',
            },
        )

        if self.context.get('zlogin_source'):
            self.symlink(
                '{zlogin_source}',
                '~/.zlogin',
                messages={
                    'before': 'Adding ~/.zlogin symlink if missing...',
                    'skip': '~/.zlogin already exists.',
                },
            )

        if self.context.get('zprofile_source'):
            self.symlink(
                '{zprofile_source}',
                '~/.zprofile',
                messages={
                    'before': 'Adding ~/.zprofile symlink if missing...',
                    'skip': '~/.zprofile already exists.',
                },
            )

        if self.context.get('zshenv_source'):
            self.symlink(
                '{zshenv_source}',
                '~/.zshenv',
                messages={
                    'before': 'Adding ~/.zshenv symlink if missing...',
                    'skip': '~/.zshenv already exists.',
                },
            )

        if self.context.get('zsh_theme_source'):
            self.symlink(
                '{zsh_theme_source}',
                '{zsh_theme_target}',
                messages={
                    'before': 'Adding ZSH theme symlink {zsh_theme_target} if missing...',
                    'skip': '{zsh_theme_target} already exists.',
                },
            )

        if default_shell:
            self.change_shell(
                '{user}', '/usr/bin/zsh',
                messages={
                    'before': 'Changing user shell to ZSH as needed...',
                    'skip': 'Shell is already ZSH.',
                },
            )

    def setup_neovim(self):
        """
        Install and configure NeoVim for user.

        Symbols consumed:
        * vimrc_source
        """

        with self.sub_script(vimrc_target='~/.config/nvim/init.vim') as sub_script:

            sub_script.apt_install('/usr/bin/nvim', 'neovim')

            sub_script.create_folder('~/.config/nvim')
            sub_script.create_folder('~/.local/share/nvim')

            sub_script.symlink(
                '{vimrc_source}',
                '{vimrc_target}',
                messages={
                    'before': 'Adding NeoVim symlink {vimrc_target} if missing...',
                    'skip': '{vimrc_target} already exists.',
                },
            )

    def setup_inputrc(self):
        """
        Configure ~/.inputrc by symlinking to one from configuration repository.

        Symbols consumed:
        * inputrc_source
        """
        self.symlink(
            '{inputrc_source}',
            '~/.inputrc',
            messages={
                'before': 'Adding ~/.inputrc symlink if missing...',
                'skip': '~/.inputrc already exists.',
            },
        )

    def synchronize_files(self,
                          source_path_or_paths: Union[str, Sequence[str]],
                          target_path: str,
                          skip_existing: bool = False,
                          quiet: bool = False,
                          ):
        """
        Front end to scripted rsync command with simplified options.

        As with rsync itself, trailing slashes should be used when synchronizing
        folders.

        :param source_path_or_paths: source path(s) using rsync syntax if host is specified
        :param target_path: target path using rsync syntax if host is specified
        :param skip_existing: don't overwrite existing files
        :param quiet: suppress non-error messages
        """
        options: List[str] = ['--archive']
        if Options.dry_run:
            options.append('--dry-run')
        if Options.debug or Options.verbose:
            options.append('--verbose')
        elif quiet:
            options.append('--quiet')
        if skip_existing:
            options.append('--ignore-existing')
        option_string = f'{" ".join(options)} ' if options else ''
        quoted_target_path = shell_quote_arg(target_path)
        quoted_source_paths = ' '.join([
            shell_quote_arg(path) for path in make_list(source_path_or_paths)])
        with self.sub_script(quoted_target_path=quoted_target_path,
                             quoted_source_paths=quoted_source_paths,
                             option_string=option_string,
                             ) as sub_script:
            sub_script.action(
                '''
                rsync {option_string}{quoted_source_paths} {quoted_target_path}
                ''',
                messages={
                    'before': 'Synchronizing files: {quoted_source_paths} -> {quoted_target_path}',
                }
            )

    def execute_local(self):
        """Execute script locally, i.e. on client."""
        self.execute()

    def execute_remote(self, host: str = None, user: str = None):
        """
        Execute script on remote host.

        :param host: optional host override (default: {host})
        :param user: optional user override (default: {user})
        """
        self.execute(host=host or '{host}', user=user or '{user}')
