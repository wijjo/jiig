"""Alias sub-command tasks."""

from typing import Text, Iterator, Iterable

from jiig import arg, task, sub_task, argument, TaskRunner

from jiig.internal.aliases import AliasManager, Alias

from jiig.utility.general import format_table
from jiig.utility.console import log_message, log_error


@task('alias',
      description='Manage command aliases',
      auxiliary_task=True)
def task_alias(_runner: TaskRunner):
    pass


@sub_task(task_alias, 'delete',
          argument('ALIAS', arg.text,
                   description='Name of alias to delete'),
          description='Delete alias')
def task_alias_delete(runner: TaskRunner):
    with AliasManager() as manager:
        manager.delete_alias(runner.args.ALIAS)


@sub_task(task_alias, 'description',
          argument('ALIAS', arg.text,
                   description='Name of alias to update'),
          argument('DESCRIPTION', arg.text,
                   description='Alias description',
                   cardinality='+'),
          description='Set alias description')
def task_alias_description(runner: TaskRunner):
    with AliasManager() as manager:
        description = ' '.join(runner.args.DESCRIPTION)
        manager.update_alias(runner.args.ALIAS, description=description)


@sub_task(task_alias, 'list',
          argument('EXPAND_NAMES', arg.boolean,
                   description='Display expanded paths in names',
                   flags=('-e', '--expand-names')),
          description='List aliases')
def task_alias_list(runner: TaskRunner):
    displayed_line_count = 0
    with AliasManager() as manager:
        for line in _format_aliases(manager.iterate_aliases(),
                                    long_names=runner.args.EXPAND_NAMES):
            log_message(line)
            displayed_line_count += 1
    # _format_aliases() returns no lines, not even a heading, if no aliases exist.
    if displayed_line_count == 0:
        log_message('No aliases exist.')


@sub_task(task_alias, 'rename',
          argument('ALIAS', arg.text,
                   description='Existing alias name'),
          argument('ALIAS_NEW', arg.text,
                   description='New alias name'),
          description='Rename alias')
def task_alias_rename(runner: TaskRunner):
    with AliasManager() as manager:
        manager.rename_alias(runner.args.ALIAS, runner.args.ALIAS_NEW)


@sub_task(task_alias, 'set',
          argument('DESCRIPTION', arg.text,
                   description='New alias description',
                   flags=('-d', '--description')),
          argument('ALIAS', arg.text,
                   description='Name of alias to create or update'),
          argument('COMMAND', arg.text,
                   description='Command with options and arguments'),
          description='Create or update alias',
          # The command to alias is fed as unparsed trailing arguments.
          receive_trailing_arguments=True)
def task_alias_set(runner: TaskRunner):
    with AliasManager() as manager:
        if manager.resolve_alias(runner.args.ALIAS):
            manager.update_alias(runner.args.ALIAS,
                                 command=[runner.args.COMMAND] + runner.trailing_args,
                                 description=runner.args.DESCRIPTION)
        else:
            manager.create_alias(runner.args.ALIAS,
                                 [runner.args.COMMAND] + runner.trailing_args,
                                 description=runner.args.DESCRIPTION)


@sub_task(task_alias, 'show',
          argument('ALIASES', arg.text,
                   description='Alias name(s) to display',
                   cardinality='+'),
          description='Display alias')
def task_alias_show(runner: TaskRunner):
    def _generate_aliases() -> Iterator[Alias]:
        for name in runner.args.ALIASES:
            alias = manager.resolve_alias(name)
            if alias is not None:
                yield alias
            else:
                log_error(f'Alias "{name}" does not exist.')
    with AliasManager() as manager:
        for line in _format_aliases(_generate_aliases()):
            log_message(line)


def _format_aliases(aliases: Iterable[Alias], long_names=False) -> Iterator[Text]:
    # Keep alias labels grouped and sorted by path within the group.
    raw_rows = sorted([
        (alias.name if long_names else alias.short_name,
         alias.description,
         alias.command_string,
         alias.label,
         (alias.path if long_names else alias.short_path) or '')
        for alias in aliases
    ], key=lambda row: (row[3], row[4]))
    if raw_rows:
        rows = [row[:3] for row in raw_rows]
        for line in format_table(*rows, headers=['alias', 'description', 'command']):
            yield line
