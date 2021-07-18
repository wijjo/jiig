"""
Scripter for provisioning actions.
"""

import os
from typing import Union, Sequence

from jiig import Script
from jiig.util.general import make_list

from .folders import script_folder_creation
from .files import script_symlink_creation
from .git import script_clone_git_repository
from .packages import script_apt_package_installation
from .users import script_user_shell_selection


def script_user_bash_configuration(script: Script,
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
        script_user_shell_selection(script, user, '/bin/bash')


def script_user_zsh_setup(script: Script,
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
    script_apt_package_installation(script, '/usr/bin/zsh', 'zsh', 'zsh-doc')
    script_symlink_creation(script, rc_source, '~/.zshrc')
    if login_source:
        script_symlink_creation(script, login_source, '~/.zlogin')
    if profile_source:
        script_symlink_creation(script, profile_source, '~/.zprofile')
    if env_source:
        script_symlink_creation(script, env_source, '~/.zshenv')
    if theme_source:
        if theme_source and not theme_target:
            theme_target = f'~/.{os.path.basename(theme_source)}'
        script_symlink_creation(script, theme_source, theme_target)
    if default_shell:
        script_user_shell_selection(script, user, '/usr/bin/zsh')
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


def script_user_neovim_setup(script: Script,
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
    script_apt_package_installation(script, '/usr/bin/nvim', 'neovim')
    script_folder_creation(script, '~/.config/nvim')
    script_folder_creation(script, '~/.local/share/nvim')
    script_symlink_creation(script, rc_source, rc_target)
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


def script_readline_configuration(script: Script,
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


def script_user_pyenv_setup(script: Script, enable_betas: bool = False):
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
    script_apt_package_installation(
        script,
        'make', 'build-essential', 'libssl-dev', 'zlib1g-dev',
        'libbz2-dev', 'libreadline-dev', 'libsqlite3-dev', 'wget',
        'curl', 'llvm', 'libncursesw5-dev', 'xz-utils', 'tk-dev',
        'libxml2-dev', 'libxmlsec1-dev', 'libffi-dev', 'liblzma-dev',
    )
    with script.block(
        predicate='[[ ! -e ~/.pyenv ]]',
        messages={
            'before': 'Cloning ~/.pyenv...',
            'skip': '~/.pyenv already exists.'
        },
    ):
        script_clone_git_repository(script, 'https://github.com/pyenv/pyenv.git', '~/.pyenv')
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


def script_install_git_project(script: Script,
                               repo_url: str,
                               repo_folder: str,
                               executables: Union[str, Sequence[str]],
                               bin_folder: str = None,
                               flat: bool = False,
                               ):
    """
    Clone a Git repository and hook project assets into the local environment.

    Assumes bin_folder or ~/bin will be in the user path, if present. Executable
    symlinks are placed in the bin folder to make them available for shell use.

    :param script: script to receive actions
    :param repo_url: repository URL
    :param repo_folder: local repository folder
    :param executables: executable(s) to install as symlinks in bin folder
    :param bin_folder: target folder for executable symlinks (default: ~/bin)
    :param flat: omit --recurse-submodules flag if True
    """
    script_clone_git_repository(script, repo_url, repo_folder, flat=flat)
    if not bin_folder:
        bin_folder = '~/bin'
    executables = make_list(executables)
    if executables:
        create_folder = True
        for executable in executables:
            source_path = os.path.join(repo_folder, executable)
            target_path = os.path.join(bin_folder, os.path.basename(executable))
            script_symlink_creation(script, source_path, target_path,
                                    create_folder=create_folder)
            # Only need to attempt parent folder creation once.
            create_folder = False
