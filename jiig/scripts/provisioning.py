"""
Scripter provisioning script.
"""

import os
from typing import List

from jiig.util.general import plural
from jiig.util.git import repo_name_from_url
from jiig.util.process import shell_quote_path

from .shell import ShellScript


class ProvisioningScript(ShellScript):
    """Script that can perform local and remote provisioning tasks."""

    def create_user(self, user: str, *groups: str, messages: dict = None):
        """
        Add user creation to script.

        :param user: user to create
        :param groups: user assigned groups
        :param messages: output messages (defaults provided)
        """
        if messages is None:
            messages = {
                'before': f'Creating user (as needed): {user}',
                'skip': f'User "{user}" already exists.',
            }
        with self.block(predicate=f'! grep -q ^{user}: /etc/passwd', messages=messages):
            self.action(
                [
                    self._wrap_command(f'adduser {user}', need_root=True)
                ] + [
                    self._wrap_command(f'usermod -aG %s {user}' % group, need_root=True)
                    for group in groups
                ],
                messages=messages,
            )

    def setup_ssh_key(self, key_path: str = None, label: str = None, messages: dict = None):
        """
        Generate SSH key pair as needed.

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
        with self.block(
            predicate=f'[[ ! -f {key_path} ]]',
            messages=messages,
        ):
            self.action(
                f'ssh-keygen{option_string}',
                messages=messages,
            )

    def install_ssh_key(self, host: str, user: str, key_path: str, messages: dict = None):
        """
        Install SSH public key on host.

        :param host: host name or address
        :param user: user name
        :param key_path: key file base path
        :param messages: output messages (defaults provided)
        """
        if messages is None:
            messages = {
                'before': f'Copying SSH key to {user}@{host}: {key_path}',
            }
        self.action(
            f'ssh-copy-id -i {key_path}.pub {user}@{host}',
            messages=messages,
        )

    def test_git_connection(self, key_path: str = None):
        """
        Test Git connection and display public key if it fails.

        :param key_path: base SSH key file path
        """
        key_path = key_path or '~/.ssh/id_rsa'
        with self.block(
            predicate='! {{ ssh -T git@github.com || [ $? -eq 1 ]; }}',
            messages={
                'before': 'Checking that Git connection works...',
                'skip': 'Git connection was successful.',
            },
        ):
            self.action(
                f'''
                cat {key_path}.pub
                echo "Add the above key to GitHub (https://github.com/settings/keys)."
                read -p "Press Enter to continue:"
                ''',
            )

    def git_clone(self, repo_url: str, repo_folder: str, flat: bool = False):
        """
        Clone local Git repository.

        :param repo_url: repository URL
        :param repo_folder: local repository folder
        :param flat: omit --recurse-submodules flag if True
        """
        option_string = ' --recurse-submodules' if not flat else ''
        self.create_parent_folder(repo_folder)
        quoted_repo_folder = shell_quote_path(repo_folder)
        with self.block(
            predicate=f'[[ ! -d {quoted_repo_folder} ]]',
            messages={
                'before': f'Cloning Git repository folder (as needed): {repo_folder}',
                'skip': f'Local repository folder {repo_folder} exists.',
            },
        ):
            self.action(f'git clone{option_string} {repo_url} {quoted_repo_folder}')

    def setup_git(self,
                  host_ssh_key: str = None,
                  config_repo_url: str = None,
                  config_folder: str = None,
                  config_source: str = None,
                  ):
        """
        Install and configure Git for user.

        Optionally clone configuration repository and symlink to ~/.gitconfig
        source file.

        :param host_ssh_key: SSH key path (default: ~/.ssh/id_rsa)
        :param config_repo_url: optional configuration repository URL
        :param config_folder: optional local configuration repository folder
        :param config_source: optional path to ~/.gitconfig symlink source file
        """
        self.apt_install('/usr/bin/git', 'git')
        self.setup_ssh_key(key_path=host_ssh_key)
        self.test_git_connection(key_path=host_ssh_key)
        if config_repo_url:
            if not config_folder:
                config_folder = f'~/{repo_name_from_url(config_repo_url)}'
            self.git_clone(config_repo_url, config_folder)
        if config_source:
            self.symlink(config_source, '~/.gitconfig')

    def setup_network_tools(self,):
        """Install curl and wget."""
        self.apt_install('/usr/bin/curl', 'curl')
        self.apt_install('/usr/bin/wget', 'wget')
        self.apt_install('/usr/bin/rsync', 'rsync')

    def apt_install(self, executable: str, *packages: str, messages: dict = None):
        """
        Install package(s) using apt.

        Override Script method to provide default messages.

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
        with self.block(
            predicate=f'! command -v {executable} > /dev/null',
            messages=messages,
        ):
            self.action(
                self._wrap_command(f'apt install -y {packages_string}', need_root=True),
                messages=messages,
            )

    def change_shell(self, user: str, shell: str, messages: dict = None):
        """
        Add user shell changing to script.

        :param user: user name
        :param shell: shell to assign
        :param messages: output messages
        """
        if messages is None:
            messages = {
                'before': f'Changing shell for user "{user}" (as needed): {shell}',
                'skip': f'Shell is already {shell}.'
            }
        with self.block(
            predicate=f'[[ $SHELL != {shell} ]]',
            messages=messages,
        ):
            self.action(
                self._wrap_command(f'chsh -s {shell} {user}', need_root=True),
                messages=messages,
            )

    def setup_bash(self, user: str, rc_source: str, default_shell: bool = False):
        """
        Configure bash for user.

        :param user: user name
        :param rc_source: ~/.bashrc source path
        :param default_shell: make Bash the user shell if True
        """
        bashrc_command = f'test -f {rc_source} && source {rc_source}'
        with self.block(
            predicate=f'! grep -q {rc_source} ~/.bashrc',
            messages={
                'before': 'Hooking up ~/.bashrc as needed...',
                'skip': '~/.bashrc is already hooked up.',
            },
        ):
            self.action(f"echo -e '\\n{bashrc_command}' >> ~/.bashrc")
        if default_shell:
            self.change_shell(user, '/bin/bash')

    def setup_zsh(self,
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

        NB: The oh-my-zsh option assumes the ~/.zshrc source file is
        pre-configured for oh-my-zsh. It undoes the oh-my-zsh ~/.zshrc changes.

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
        self.apt_install('/usr/bin/zsh', 'zsh', 'zsh-doc')
        self.symlink(rc_source, '~/.zshrc')
        if login_source:
            self.symlink(login_source, '~/.zlogin')
        if profile_source:
            self.symlink(profile_source, '~/.zprofile')
        if env_source:
            self.symlink(env_source, '~/.zshenv')
        if theme_source:
            if theme_source and not theme_target:
                theme_target = f'~/.{os.path.basename(theme_source)}'
            self.symlink(theme_source, theme_target)
        if default_shell:
            self.change_shell(user, '/usr/bin/zsh')
        if oh_my_zsh:
            with self.block(
                predicate='[[ ! -e ~/.oh-my-zsh ]]',
                messages={
                    'before': 'Installing oh-my-zsh as needed...',
                    'skip': 'oh-my-zsh is already installed.',
                },
            ):
                self.action(
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

    def setup_neovim(self, rc_source: str, install_plugins: bool = False):
        """
        Install and configure NeoVim for user.

        :param rc_source: ~/.config/nvim/init.vim source path
        :param install_plugins: install plugins if True
        """
        rc_target = '~/.config/nvim/init.vim'
        vundle_url = 'https://github.com/VundleVim/Vundle.vim.git'
        vundle_path = '~/.local/share/nvim/bundle/Vundle.vim'
        self.apt_install('/usr/bin/nvim', 'neovim')
        self.create_folder('~/.config/nvim')
        self.create_folder('~/.local/share/nvim')
        self.symlink(rc_source, rc_target)
        if install_plugins:
            with self.block(
                predicate=f'[[ ! -d {vundle_path} ]]',
                messages={
                    'before': 'Installing NeoVim plugins as needed...',
                    'skip': 'NeoVim plugin folder already exists.',
                },
            ):
                self.action(
                    f'''
                    git clone {vundle_url} {vundle_path}
                    nvim +PluginInstall +qall
                    ''',
                )

    def setup_readline(self,
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
        with self.block(
            predicate='[[ ! -e ~/.inputrc ]]',
            messages={
                'before': 'Generating ~/.inputrc...',
                'skip': '~/.inputrc already exists.'
            },
        ):
            self.action(f'echo "{body}" > ~/.inputrc')
