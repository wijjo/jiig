"""
Package provisioning.
"""

from jiig import Script
from jiig.util.general import plural


def script_apt_package_installation(script: Script,
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
