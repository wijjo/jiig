import os
from typing import List

from .messages import Messages
from .script import Script


class ProvisioningScript(Script):

    def __init__(self,
                 dry_run: bool = False,
                 debug: bool = False,
                 pause: bool = False,
                 unchecked: bool = False,
                 need_sudo: bool = False,
                 blocks: List[str] = None,
                 ):
        super().__init__(dry_run=dry_run,
                         debug=debug,
                         pause=pause,
                         unchecked=unchecked,
                         need_sudo=need_sudo,
                         blocks=blocks,
                         )

    def setup_git(self):
        """
        Install and configure Git for user.

        Symbols consumed:
        * ssh_key
        * config_folder
        * gitconfig_source
        """

        self.apt_install(
            '/usr/bin/git', 'git',
            messages=Messages(
                heading='Installing Git as needed with apt...',
                skip='Git is already installed.',
            ),
        )

        self.action(
            '''
            ssh-keygen -f {ssh_key}
            ''',
            predicate='[[ ! -f {ssh_key} ]]',
            messages=Messages(
                heading='Making sure SSH key {ssh_key} is available...',
                skip='SSH keys exist.',
            ),
        )

        self.action(
            '''
            cat {ssh_key}.pub
            echo "Add the above key to GitHub (https://github.com/settings/keys)."
            read -p "Press Enter to continue:"
            ''',
            predicate='! {{ ssh -T git@github.com || [ $? -eq 1 ]; }}',
            messages=Messages(
                heading='Checking that Git connection works...',
                skip='Git connection was successful.',
            ),
        )

        parent_folder = os.path.dirname(self.scripter.format('{config_folder}'))
        self.create_folder(
            parent_folder,
            messages=Messages(
                heading=f'Making sure configuration repository folder {parent_folder} exists...',
                skip=f'Configuration repository source folder {parent_folder} exists.',
            ),
        )

        self.action(
            '''
            git clone --recurse-submodules {config_repo_url}
            ''',
            predicate='[[ ! -d {config_folder} ]]',
            location=f'{parent_folder}',
            messages=Messages(
                heading='Cloning configuration folder {config_folder} as needed...',
                skip='Configuration folder {config_folder} exists.',
            ),
        )

        self.symlink(
            '{gitconfig_source}', '~/.gitconfig',
            messages=Messages(
                heading='Adding ~/.gitconfig symlink if missing...',
                skip='~/.gitconfig already exists.',
            ),
        )

    def setup_network_tools(self):
        """
        Install curl and wget.

        No symbols consumed.
        """
        self.apt_install(
            '/usr/bin/curl', 'curl',
            messages=Messages(
                heading='Installing curl as needed with apt...',
                skip='Curl is already installed.',
            ),
        )
        self.apt_install(
            '/usr/bin/wget', 'wget',
            messages=Messages(
                heading='Installing wget as needed with apt...',
                skip='Wget is already installed.',
            ),
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
                messages=Messages(
                    heading='Hooking up ~/.bashrc as needed...',
                    skip='~/.bashrc is already hooked up.',
                ),
            )

        if default_shell:
            self.change_shell(
                '{user}', '/bin/bash',
                messages=Messages(
                    heading='Changing user shell to Bash as needed...',
                    skip='Shell is already Bash.',
                )
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
        self.apt_install(
            '/usr/bin/zsh', 'zsh', 'zsh-doc',
            messages=Messages(
                heading='Installing ZSH as needed with apt...',
                skip='ZSH is already installed.',
            ),
        )

        self.symlink(
            '{zshrc_source}',
            '~/.zshrc',
            messages=Messages(
                heading='Adding ~/.zshrc symlink if missing...',
                skip='~/.zshrc already exists.',
            ),
        )

        if self.scripter.get('zlogin_source'):
            self.symlink(
                '{zlogin_source}',
                '~/.zlogin',
                messages=Messages(
                    heading='Adding ~/.zlogin symlink if missing...',
                    skip='~/.zlogin already exists.',
                ),
            )

        if self.scripter.get('zprofile_source'):
            self.symlink(
                '{zprofile_source}',
                '~/.zprofile',
                messages=Messages(
                    heading='Adding ~/.zprofile symlink if missing...',
                    skip='~/.zprofile already exists.',
                ),
            )

        if self.scripter.get('zshenv_source'):
            self.symlink(
                '{zshenv_source}',
                '~/.zshenv',
                messages=Messages(
                    heading='Adding ~/.zshenv symlink if missing...',
                    skip='~/.zshenv already exists.',
                ),
            )

        if self.scripter.get('zsh_theme_source'):
            self.symlink(
                '{zsh_theme_source}',
                '{zsh_theme_target}',
                messages=Messages(
                    heading='Adding ZSH theme symlink {zsh_theme_target} if missing...',
                    skip='{zsh_theme_target} already exists.',
                ),
            )

        if default_shell:
            self.change_shell(
                '{user}', '/usr/bin/zsh',
                messages=Messages(
                    heading='Changing user shell to ZSH as needed...',
                    skip='Shell is already ZSH.',
                )
            )

    def setup_neovim(self):
        """
        Install and configure NeoVim for user.

        Symbols consumed:
        * vimrc_source
        """

        with self.sub_script(vimrc_target='~/.config/nvim/init.vim') as sub_script:

            sub_script.apt_install(
                '/usr/bin/nvim', 'neovim',
                messages=Messages(
                    heading='Installing NeoVim as needed with apt...',
                    skip='NeoVim is already installed.',
                ),
            )

            sub_script.create_folder('~/.config/nvim')
            sub_script.create_folder('~/.local/share/nvim')

            sub_script.symlink(
                '{vimrc_source}',
                '{vimrc_target}',
                messages=Messages(
                    heading='Adding NeoVim symlink {vimrc_target} if missing...',
                    skip='{vimrc_target} already exists.',
                ),
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
            messages=Messages(
                heading='Adding ~/.inputrc symlink if missing...',
                skip='~/.inputrc already exists.',
            ),
        )
