"""
Scripter for provisioning actions.
"""

from jiig import Script


def script_user_creation(script: Script,
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


def script_user_shell_selection(script: Script,
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
