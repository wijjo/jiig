"""Alias sub-command tasks."""

from typing import Text, Iterator, Iterable

from jiig import task, TaskRunner
from jiig.internal.aliases import AliasManager, Alias
from jiig.utility.general import format_table
from jiig.utility.console import log_message, log_error


@task('alias',
      help='manage command aliases',
      auxiliary_task=True)
def task_alias(_runner: TaskRunner):
    pass


@task(
    name='delete',
    parent=task_alias,
    help='delete alias',
    arguments=[
        {'dest': 'ALIAS',
         'help': 'name of alias to delete'},
    ],
)
def task_alias_delete(runner: TaskRunner):
    with AliasManager() as manager:
        manager.delete_alias(runner.args.ALIAS)


@task(
    name='description',
    parent=task_alias,
    help='set alias description',
    arguments=[
        {'dest': 'ALIAS',
         'help': 'name of alias to update with a description'},
        {'dest': 'DESCRIPTION',
         'nargs': '+',
         'help': 'description text (multiple arguments allowed)'},
    ],
)
def task_alias_description(runner: TaskRunner):
    with AliasManager() as manager:
        description = ' '.join(runner.args.DESCRIPTION)
        manager.update_alias(runner.args.ALIAS, description=description)


@task(
    name='list',
    parent=task_alias,
    help='list aliases',
    options={
        ('-e', '--expand-names'): {'dest': 'EXPAND_NAMES',
                                   'action': 'store_true',
                                   'help': 'display expanded paths in names'},
    },
)
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


@task(
    name='rename',
    parent=task_alias,
    help='rename alias',
    arguments=[
        {'dest': 'ALIAS',
         'help': 'name of alias to rename'},
        {'dest': 'ALIAS_NEW',
         'help': 'new alias name'},
    ],
)
def task_alias_rename(runner: TaskRunner):
    with AliasManager() as manager:
        manager.rename_alias(runner.args.ALIAS, runner.args.ALIAS_NEW)


@task(
    name='set',
    parent=task_alias,
    help='create or update alias',
    options={
        ('-d', '--description'): {'dest': 'DESCRIPTION',
                                  'help': 'alias description'},
    },
    arguments=[
        {'dest': 'ALIAS',
         'help': 'name of alias to create or update'},
        {'dest': 'COMMAND',
         'help': 'command with options and arguments'},
    ],
    # The command to alias is fed as unparsed trailing arguments.
    trailing_arguments=True,
)
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


@task(
    name='show',
    parent=task_alias,
    help='display alias',
    arguments=[
        {'dest': 'ALIASES',
         'nargs': '+',
         'help': 'alias name(s) to display'},
    ],
)
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
