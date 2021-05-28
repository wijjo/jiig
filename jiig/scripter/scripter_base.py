import os
from contextlib import contextmanager
from subprocess import CompletedProcess, run
from typing import ContextManager, Optional, Any, Union, Sequence, List

from .messages import Messages
from .context import Context


class ScripterBase:
    """
    Base script-building support.

    Also provides various related utility methods, including script text
    manipulation and immediate command execution.

    The output methods, like heading, message, etc., provide added value over
    util.console functions by performing symbol expansion.
    """

    def __init__(self,
                 debug: bool = False,
                 dry_run: bool = False,
                 pause: bool = False,
                 **kwargs,
                 ):
        """
        Construct base scripter.

        :param debug: enable debug output
        :param dry_run: do not execute destructive commands
        :param pause: pause before executing scripts
        :param kwargs: keyword argument symbols
        """
        self.debug = debug
        self.dry_run = dry_run
        self.pause = pause
        self.context = Context(self.debug)
        # Strings in kwargs are sequentially expanded by update().
        self.context.update(**kwargs)
        # Separate update for nl is needed to avoid "multiple values" error when cloning a scripter.
        self.context.copy_symbols(nl=os.linesep)

    @contextmanager
    def sub_scripter(self, **kwargs) -> ContextManager['ScripterBase']:
        # kwargs need to be expanded using self.context.symbols, which don't need to be expanded.
        child_scripter = self.__class__(debug=self.debug,
                                        dry_run=self.dry_run,
                                        pause=self.pause)
        child_scripter.context.copy_symbols(**self.context.symbols)
        if kwargs:
            child_scripter.update(**kwargs)
        yield child_scripter

    def copy_symbols(self, **kwargs):
        self.context.copy_symbols(**kwargs)

    def update(self, **kwargs):
        self.context.update(**kwargs)

    def format(self, text: str) -> str:
        return self.context.format(text)

    def get(self, name: str) -> Optional[Any]:
        return self.context.get(name)

    def heading(self, message: str):
        self.context.heading(message)

    def message(self, message: Optional[str], *args, **kwargs):
        self.context.message(message, *args, **kwargs)

    def warning(self, message: Optional[str], *args, **kwargs):
        self.context.warning(message, *args, **kwargs)

    def error(self, message: Optional[str], *args, **kwargs):
        self.context.error(message, *args, **kwargs)

    def abort(self, message: Optional[str], *args, **kwargs):
        self.context.abort(message, *args, **kwargs)

    def format_command(self,
                       command_string_or_sequence: Union[str, Sequence],
                       indent: int = None,
                       double_spaced: bool = False,
                       ) -> str:
        return self.context.format_command(command_string_or_sequence,
                                           indent=indent,
                                           double_spaced=double_spaced)

    def format_script(self,
                      command_string_or_sequence: Union[str, Sequence],
                      location: str = None,
                      predicate: str = None,
                      messages: Messages = None,
                      ) -> str:
        return self.context.script(command_string_or_sequence,
                                   location=location,
                                   predicate=predicate,
                                   messages=messages,
                                   )

    def run(self,
            command: Union[str, Sequence],
            predicate: str = None,
            capture: bool = False,
            unchecked: bool = False,
            ignore_dry_run: bool = False,
            messages: Messages = None,
            ) -> CompletedProcess:

        if messages is None:
            messages = Messages()

        with self.sub_scripter(command=command, predicate=predicate) as sub_scripter:

            full_command = sub_scripter.get('command')

            if messages.heading:
                sub_scripter.heading(messages.heading)

            sub_scripter.message('command: {command}')
            if predicate:
                sub_scripter.message('predicate: {predicate}')

            if self.dry_run and not ignore_dry_run:
                return CompletedProcess([full_command], 0)

            if predicate is not None:
                predicate_command = sub_scripter.get('predicate')
                predicate_proc = run(predicate_command, shell=True)
                if predicate_proc.returncode != 0:
                    if messages.skip:
                        sub_scripter.message(messages.skip)
                return CompletedProcess([full_command], 0)

            run_kwargs = dict(shell=True)
            if capture:
                run_kwargs.update(capture_output=True, encoding='utf-8')

            proc = run(full_command, **run_kwargs)

            if proc.returncode == 0:
                if messages.success:
                    sub_scripter.message(messages.success)
            else:
                if messages.failure:
                    sub_scripter.message(messages.failure)
                if not unchecked:
                    sub_scripter.abort('Command failed.')

            return proc

    def pipe(self, raw_command: Union[str, List]) -> str:
        proc = self.run(raw_command, capture=True, unchecked=False, ignore_dry_run=True)
        return proc.stdout.strip()

    def pipe_lines(self, raw_command: Union[str, List]) -> List[str]:
        return self.pipe(raw_command).split(os.linesep)
