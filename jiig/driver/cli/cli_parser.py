# Copyright (C) 2021-2023, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

"""CLI parser based on argparse standard library module."""

import argparse
import os
import re
import sys
from contextlib import contextmanager
from typing import Sequence, Any

from jiig.util.collections import make_list
from jiig.util.default import DefaultValue
from jiig.util.log import Logger
from jiig.util.python import format_call_string
from jiig.util.repetition import Repetition

from .cli_types import CLICommand, CLIOptionArgument

DEST_NAME_SEPARATOR = '.'
REQUIRED_SUB_COMMAND_REGEX = re.compile(r'^the following arguments are required: (.*)$')


logger = Logger(sub_tag='argparse')


class CLIParserError(Exception):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    """Wrap the argparse class to add debugging and some default values."""

    raise_exceptions = False
    debug = False
    see_help_message = '(see tool help or documentation for more information)'

    def __init__(self,
                 prog: str = None,
                 description: str = None,
                 add_help: bool = False,
                 ):
        self._command_names = []
        try:
            super().__init__(prog=prog, description=description, add_help=add_help)
        except Exception as exc:
            self._abort('ArgumentParser', exc)

    def add_subparsers(self, *args, **kwargs):
        """Overridden for logging and exception handling.

        Args:
            *args: argparse.ArgumentParser.add_subparsers() positional arguments
            **kwargs: argparse.ArgumentParser.add_subparsers() keyword arguments
        """
        self.dump('add_subparsers', *args, **kwargs)
        try:
            _parser = self
            _group = super().add_subparsers(*args, **kwargs)

            class _GroupWrapper:

                @staticmethod
                def add_parser(*group_args, **group_kwargs):
                    sub_parser = _group.add_parser(*group_args, **group_kwargs)
                    if group_args:
                        sub_parser._command_names = _parser._command_names + [group_args[0]]
                    if self.debug:
                        _parser.dump(f'subparsers[{kwargs.get("dest")}].add_parser',
                                     *group_args, **group_kwargs,
                                     returned=f'ArgumentParser({id(sub_parser)})')
                    return sub_parser

                def __getattr__(self, name):
                    return getattr(_group, name)

                def __setattr__(self, name, value):
                    setattr(_group, name, value)

            return _GroupWrapper()
        except Exception as exc:
            self._abort('add_subparsers', exc, *args, **kwargs)

    def add_argument(self, *args, **kwargs):
        """Overridden for logging and exception handling.

        Args:
            *args: argparse.ArgumentParser.add_argument() positional arguments
            **kwargs: argparse.ArgumentParser.add_argument() keyword arguments
        """
        # Remove any keywords that argparse does not handle.
        if 'common_footnotes' in kwargs:
            del kwargs['common_footnotes']
        if self.debug:
            self.dump('add_argument', *args, **kwargs)
        try:
            return super().add_argument(*args, **kwargs)
        except Exception as exc:
            self._abort('add_argument', exc, *args, **kwargs)

    def parse_args(self,
                   args: Sequence = None,
                   namespace: argparse.Namespace = None,
                   raise_exceptions: bool = False
                   ) -> argparse.Namespace:
        """Overridden for logging and exception handling.

        Args:
            args: command line arguments
            namespace: incoming namespace
            raise_exceptions: raise exceptions if True
        """
        if self.debug:
            self.dump('parse_args',
                      args=args,
                      namespace=namespace,
                      raise_exceptions=raise_exceptions)
        if raise_exceptions:
            with self._exceptions():
                return super().parse_args(args=args, namespace=namespace)
        else:
            return super().parse_args(args=args, namespace=namespace)

    def parse_known_args(self,
                         args: Sequence = None,
                         namespace: argparse.Namespace = None,
                         raise_exceptions: bool = False
                         ) -> tuple[argparse.Namespace, list[str]]:
        """Overridden for logging and exception handling.

        Args:
            args: command line arguments
            namespace: incoming namespace
            raise_exceptions: raise exceptions if True
        """
        if self.debug:
            self.dump('parse_known_args',
                      args=args,
                      namespace=namespace,
                      raise_exceptions=raise_exceptions)
        if raise_exceptions:
            with self._exceptions():
                return super().parse_known_args(args=args, namespace=namespace)
        else:
            return super().parse_known_args(args=args, namespace=namespace)

    def error(self, message: str):
        """Error handling.

        Args:
            message: error message

        Raises:
            CLIParserError: if any error occurs
        """
        if self.raise_exceptions:
            raise CLIParserError(message)
        if REQUIRED_SUB_COMMAND_REGEX.match(message):
            logger.message(f'Command: {self.prog}')
            logger.error(message)
            help_words = self.prog.split()
            help_words.insert(1, 'help')
            logger.message(self.see_help_message)
            sys.exit(0)
        else:
            logger.error(message)
            logger.message(self.see_help_message)
            sys.exit(2)

    def format_usage(self):
        """Format usage message."""
        return f'{self.see_help_message}{os.linesep}'

    def format_help(self):
        """Format help message."""
        return super().format_help()

    def dump(self, method_name, *args, **kwargs):
        if self.debug:
            logger.message(f'ArgumentParser[{id(self)}:{" ".join(self._command_names)}]:'
                           f' {format_call_string(method_name, *args, **kwargs)}')

    def _abort(self, method_name, exc, *args, **kwargs):
        parser = '|'.join(self._command_names) if self._command_names else '(top)'
        logger.abort(f'CLI parsing failed (argparse).',
                     parser=parser,
                     call=format_call_string(method_name, *args, **kwargs),
                     exception=str(exc))

    @classmethod
    @contextmanager
    def _exceptions(cls):
        cls.raise_exceptions = True
        try:
            yield
        finally:
            cls.raise_exceptions = False


class Parser:

    def __init__(self, top_task_dest_name: str):
        self.top_task_dest_name = top_task_dest_name
        self.parsers: dict[str, argparse.ArgumentParser] = {}

    @classmethod
    def pre_parse(cls,
                  command_line_arguments: Sequence[str],
                  raise_exceptions: bool,
                  options: Sequence[CLIOptionArgument] = None,
                  ) -> tuple[object, list[str]]:
        """Pre-parse the command line.

        Args:
            command_line_arguments: command line argument list
            raise_exceptions: raise exceptions if True
            options: optional list of options to use for pre-parsing

        Returns:
            (argument data attributes, trailing argument list) tuple
        """
        # Don't use the primary argparse parser, since it may be initialized later.
        pre_parser = _ArgumentParser()
        cls._prepare_global_options(pre_parser, options)
        data, trailing_arguments = pre_parser.parse_known_args(
            command_line_arguments, raise_exceptions=raise_exceptions)
        if getattr(data, 'DEBUG', False):
            _ArgumentParser.debug = True
        return data, trailing_arguments

    def parse(self,
              command_line_arguments: Sequence[str],
              name: str,
              description: str,
              root_command: CLICommand,
              capture_trailing: bool = False,
              raise_exceptions: bool = False,
              ) -> tuple[object, list[str], list[str]]:
        """Parse the command line.

        Args:
            command_line_arguments: command line argument list
            name: program name
            description: program description
            root_command: root command
            capture_trailing: capture trailing arguments if True
            raise_exceptions: raise exceptions if True

        Returns:
            (argument data attributes, command names, trailing arguments) tuple
        """
        parser = _ArgumentParser(name, description)
        parser.dump('parse ArgumentParser', name=name, description=description)
        self._prepare_fields(root_command, root_command.name, parser)
        self.parsers[self.top_task_dest_name] = parser

        app_commands = list(filter(lambda c: c.visibility == 0, root_command.sub_commands))
        top_group = parser.add_subparsers(dest=self.top_task_dest_name,
                                          required=bool(app_commands))
        for command in root_command.sub_commands:
            sub_parser = top_group.add_parser(command.name,
                                              help=command.description,
                                              add_help=False)
            self._prepare_recursive(command, sub_parser, self.top_task_dest_name, [command.name])

        # Parse the command line arguments.
        if capture_trailing:
            args, trailing_args = parser.parse_known_args(command_line_arguments)
        else:
            args = parser.parse_args(command_line_arguments,
                                     raise_exceptions=raise_exceptions)
            trailing_args: list[str] = []

        # Determine the active command names.
        command_dest_preamble = self.top_task_dest_name + DEST_NAME_SEPARATOR
        command_dest = ''
        for dest in dir(args):
            if ((dest == self.top_task_dest_name
                 or dest.startswith(command_dest_preamble))
                    and len(dest) > len(command_dest)):
                command_dest = dest
        if not command_dest:
            raise RuntimeError(f'Missing {self.top_task_dest_name}* member'
                               f' in argparse namespace: {args}')
        names = [name.lower() for name in command_dest.split(DEST_NAME_SEPARATOR)[1:]]
        if app_commands:
            names.append(getattr(args, command_dest))
        return args, names, trailing_args

    @classmethod
    def _add_option_or_positional(cls,
                                  parser: argparse.ArgumentParser,
                                  command_name: str,
                                  name: str,
                                  description: str,
                                  flags: Sequence[str] = None,
                                  is_boolean_option: bool = False,
                                  repeat: Repetition = None,
                                  default: DefaultValue = None,
                                  choices: Sequence = None,
                                  ):
        kwargs: dict[str, Any] = {'dest': name.upper(), 'help': description}
        if is_boolean_option:
            kwargs['action'] = 'store_true'
        if default is not None:
            kwargs['default'] = default.value
        if choices:
            kwargs['choices'] = choices
        # Convert and validate positional argument repetition to make an `nargs` value.
        if flags is None:
            if repeat is None:
                if default is not None:
                    kwargs['nargs'] = '?'
            else:
                if repeat.minimum is None or repeat.minimum == 0:
                    if repeat.maximum is None:
                        kwargs['nargs'] = '*'
                    elif repeat.maximum == 1:
                        kwargs['nargs'] = '?'
                elif repeat.minimum == 1:
                    if repeat.maximum is None:
                        kwargs['nargs'] = '+'
                elif repeat.minimum > 0:
                    if repeat.minimum == repeat.maximum:
                        kwargs['nargs'] = repeat.minimum
                if 'nargs' not in kwargs:
                    logger.error(f'Bad repeat range for "{command_name}", field "{name}".',
                                 (repeat.minimum, repeat.maximum))
        elif repeat is not None:
            kwargs['action'] = 'append'
        # Add the argument to argparse.
        parser.add_argument(*make_list(flags), **kwargs)

    @classmethod
    def _prepare_fields(cls,
                        command: CLICommand,
                        command_name: str,
                        parser: argparse.ArgumentParser,
                        ):
        for option in command.options:
            cls._add_option_or_positional(parser,
                                          command_name,
                                          option.name,
                                          option.description,
                                          flags=option.flags,
                                          is_boolean_option=option.is_boolean,
                                          repeat=option.repeat,
                                          default=option.default,
                                          choices=option.choices)
        for argument in command.positionals:
            cls._add_option_or_positional(parser,
                                          command_name,
                                          argument.name,
                                          argument.description,
                                          repeat=argument.repeat,
                                          default=argument.default,
                                          choices=argument.choices)

    @classmethod
    def _prepare_recursive(cls,
                           command: CLICommand,
                           parser: argparse.ArgumentParser,
                           parent_dest_name: str,
                           command_names: list[str] = None,
                           ):
        if command_names is None:
            command_names = []
        command_name = ' '.join(command_names)
        cls._prepare_fields(command, command_name, parser)
        if command.sub_commands:
            dest_name = DEST_NAME_SEPARATOR.join([parent_dest_name, command.name.upper()])
            sub_group = parser.add_subparsers(dest=dest_name,
                                              required=True)
            for sub_command in command.sub_commands:
                sub_parser = sub_group.add_parser(sub_command.name,
                                                  help=sub_command.description,
                                                  add_help=False)
                cls._prepare_recursive(sub_command, sub_parser, dest_name,
                                       command_names=(command_names + [sub_command.name]))

    @staticmethod
    def _prepare_global_options(parser: argparse.ArgumentParser,
                                options: Sequence[CLIOptionArgument],
                                ):
        if options:
            for option in options:
                kwargs = {}
                if option.is_boolean:
                    kwargs['action'] = 'store_true'
                parser.add_argument(*option.flags,
                                    dest=option.name.upper(),
                                    help=option.description,
                                    **kwargs)
