"""
Scripter script.
"""

import os
from contextlib import contextmanager
from typing import List, ContextManager, Union, Sequence

from jiig.util.contexts.messages import Messages
from jiig.util.general import make_list, trim_text_blocks


class Script:
    """Used to build a script piecemeal and then execute it."""

    def __init__(self,
                 unchecked: bool = False,
                 run_by_root: bool = False,
                 blocks: List[str] = None,
                 ):
        """
        Construct script.

        :param unchecked: do not check return code if True
        :param run_by_root: script will be run by root user (don't need sudo)
        :param blocks: initial script blocks (not typically used)
        """
        self.unchecked = unchecked
        self.run_by_root = run_by_root
        self.blocks: List[str] = blocks if blocks is not None else []

    def action(self,
               command_string_or_sequence: Union[str, Sequence],
               location: str = None,
               predicate: str = None,
               messages: dict = None,
               ):
        """
        Add script action.

        :param command_string_or_sequence: command or commands
        :param location: optional temporary working folder
        :param predicate: condition to test before executing commands
        :param messages: optional display messages
        """
        self.blocks.append(
            self.format_script_block(
                command_string_or_sequence,
                location=location,
                predicate=predicate,
                messages=messages,
            )
        )

    def working_folder(self, folder: str, messages: dict = None):
        """
        Set working folder in script.

        :param folder: folder switch to
        :param messages: optional display messages
        """
        self.action(f'cd {folder}', messages=messages)

    @contextmanager
    def temporary_working_folder(self,
                                 folder: str,
                                 messages: dict = None,
                                 ) -> ContextManager[None]:
        """
        Set temporary working folder in script.

        :param folder: folder to temporarily switch to
        :param messages: optional display messages
        :return: context manager that will restore working folder with popd
        """
        self.action(f'pushd {folder} > /dev/null', messages=messages)
        yield
        self.action('popd > /dev/null')

    def _wrap_command(self, command: str, need_root: bool = False) -> str:
        """
        Prefix with "sudo" as needed.

        :param command: command to wrap, e.g. with sudo
        :param need_root: prefix with sudo if True
        :return: command with sudo prefix (if the script isn't being run by root)
        """
        return f'sudo {command}' if need_root and not self.run_by_root else command

    @staticmethod
    def format_blocks(*blocks: str,
                      indent: int = None,
                      double_spaced: bool = False,
                      ) -> str:
        """
        Format text blocks.

        :param blocks: text blocks to format
        :param indent: optional indentation amount
        :param double_spaced: add extra line separators between blocks if true
        :return: formatted text
        """
        lines = trim_text_blocks(*blocks, indent=indent, double_spaced=double_spaced)
        return os.linesep.join(lines)

    @staticmethod
    def format_quoted(text: str) -> str:
        """
        Expands symbols, wraps in double quotes as needed, and escapes embedded quotes.

        :param text: text to expand, escape, and quote
        :return: quoted expanded text
        """
        if not set(text).intersection((' ', '"')):
            return text
        escaped = text.replace('"', '\\"')
        return f'"{escaped}"'

    @classmethod
    def format_script_block(cls,
                            command_string_or_sequence: Union[str, Sequence],
                            location: str = None,
                            predicate: str = None,
                            messages: dict = None,
                            ) -> str:
        """
        Format a shell script given one or more commands.

        :param command_string_or_sequence: command or commands to include in script
        :param location: optional target directory to switch to
        :param predicate: optional predicate to test before executing commands
        :param messages: messages to display before, after, and during
        :return: formatted script text
        """
        # TODO: Handle message quoting/escaping for echo statements.
        action_messages = Messages.from_dict(messages)
        output_blocks: List[str] = []
        if action_messages.before:
            output_blocks.append(
                f'echo -e "\\n=== {action_messages.before}"')
        if predicate:
            output_blocks.append(
                f'if {predicate}; then')
            indent = 4
        else:
            indent = 0
        if location:
            output_blocks.append(cls.format_blocks(
                f'cd {cls.format_quoted(location)}', indent=indent))
        commands = make_list(command_string_or_sequence)
        if commands:
            output_blocks.append(cls.format_blocks(
                    *commands, indent=indent))
            if action_messages.success and action_messages.failure:
                output_blocks.append(cls.format_blocks(
                    f'''
                    if [[ $? -eq 0 ]]; then
                        echo "{action_messages.success}"
                    else
                        echo "{action_messages.failure}"
                    fi
                    ''', indent=indent))
            elif action_messages.success and not action_messages.failure:
                output_blocks.append(cls.format_blocks(
                    f'''
                    if [[ $? -eq 0 ]]; then
                        echo "{action_messages.success}"
                    fi
                    ''', indent=indent))
            elif not action_messages.success and action_messages.failure:
                output_blocks.append(cls.format_blocks(
                    f'''
                    if [[ $? -ne 0 ]]; then
                        echo "{action_messages.failure}"
                    fi
                    ''', indent=indent))
        if predicate:
            if action_messages.skip:
                output_blocks.append(cls.format_blocks(
                    f'''
                    else
                        echo "{action_messages.skip}"
                    fi
                    '''))
            else:
                output_blocks.append(
                    'fi',
                )
        if action_messages.after:
            output_blocks.append(cls.format_blocks(
                f'echo -e "\\n{action_messages.after}"'))
        return os.linesep.join(output_blocks)

    def get_script_body(self) -> str:
        """
        Produce script body based on previously-formatted blocks.

        IMPORTANT: Clears out previous blocks to start building a new script.

        Does not include "shebang" line or shell options setting.

        :return: script body text
        """
        body_text = f'{os.linesep}{os.linesep}'.join(self.blocks)
        self.blocks = []
        return body_text
