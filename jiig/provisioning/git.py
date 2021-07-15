"""
User Git provisioning.
"""

from jiig import Script
from jiig.util.git import repo_name_from_url
from jiig.util.process import shell_quote_path

from .connections import script_ssh_key_creation
from .files import script_symlink_creation
from .folders import script_parent_folder_creation
from .packages import script_apt_package_installation


def script_git_connection_test(script: Script, key_path: str = None):
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


def script_clone_git_repository(script: Script,
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
    script_parent_folder_creation(script, repo_folder)
    quoted_repo_folder = shell_quote_path(repo_folder)
    with script.block(
        predicate=f'[[ ! -d {quoted_repo_folder} ]]',
        messages={
            'before': f'Cloning Git repository folder (as needed): {repo_folder}',
            'skip': f'Local repository folder {repo_folder} exists.',
        },
    ):
        script.action(f'git clone{option_string} {repo_url} {quoted_repo_folder}')


def script_git_configuration(script: Script,
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
    script_apt_package_installation(script, '/usr/bin/git', 'git')
    script_ssh_key_creation(script, key_path=host_ssh_key)
    script_git_connection_test(script, key_path=host_ssh_key)
    if config_repo_url:
        if not config_folder:
            config_folder = f'~/{repo_name_from_url(config_repo_url)}'
        script_clone_git_repository(script, config_repo_url, config_folder)
    if config_source:
        script_symlink_creation(script, config_source, '~/.gitconfig')
