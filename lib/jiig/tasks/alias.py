"""Alias sub-command tasks."""

from typing import Text, Iterator, Iterable

import jiig
from jiig.utility.alias_catalog import Alias
from jiig.utility.general import format_table
from jiig.utility.console import log_message, log_error


@jiig.task('alias',
           description='Manage command aliases',
           auxiliary_task=True)
def task_alias(_runner: jiig.TaskRunner):
    pass


@jiig.sub_task(task_alias,
               'delete',
               jiig.argument('ALIAS',
                             description='Name of alias to delete'),
               description='Delete alias')
def task_alias_delete(runner: jiig.TaskRunner):
    with runner.open_alias_catalog() as catalog:
        catalog.delete_alias(runner.args.ALIAS)


@jiig.sub_task(task_alias,
               'description',
               jiig.argument('ALIAS',
                             description='Name of alias to write_data'),
               jiig.argument('DESCRIPTION',
                             description='Alias description',
                             cardinality='+'),
               description='Set alias description')
def task_alias_description(runner: jiig.TaskRunner):
    with runner.open_alias_catalog() as catalog:
        description = ' '.join(runner.args.DESCRIPTION)
        catalog.update_alias(runner.args.ALIAS, description=description)


@jiig.sub_task(task_alias,
               'list',
               jiig.bool_option('EXPAND_NAMES',
                                ('-e', '--expand-names'),
                                description='Display expanded paths in names'),
               description='List aliases')
def task_alias_list(runner: jiig.TaskRunner):
    displayed_line_count = 0
    with runner.open_alias_catalog() as catalog:
        for line in _format_aliases(catalog.iterate_aliases(),
                                    long_names=runner.args.EXPAND_NAMES):
            log_message(line)
            displayed_line_count += 1
    # _format_aliases() returns no lines, not even a heading, if no aliases exist.
    if displayed_line_count == 0:
        log_message('No aliases exist.')


@jiig.sub_task(task_alias,
               'rename',
               jiig.argument('ALIAS',
                             description='Existing alias name'),
               jiig.argument('ALIAS_NEW',
                             description='New alias name'),
               description='Rename alias')
def task_alias_rename(runner: jiig.TaskRunner):
    with runner.open_alias_catalog() as catalog:
        catalog.rename_alias(runner.args.ALIAS, runner.args.ALIAS_NEW)


@jiig.sub_task(task_alias,
               'set',
               jiig.option('DESCRIPTION',
                           ('-d', '--description'),
                           description='New alias description'),
               jiig.argument('ALIAS',
                             description='Name of alias to create or write_data'),
               jiig.argument('COMMAND',
                             description='Command with options and arguments'),
               description='Create or write_data alias',
               # The command to alias is fed as unparsed trailing arguments.
               receive_trailing_arguments=True)
def task_alias_set(runner: jiig.TaskRunner):
    with runner.open_alias_catalog() as catalog:
        if catalog.resolve_alias(runner.args.ALIAS):
            catalog.update_alias(runner.args.ALIAS,
                                 command=[runner.args.COMMAND] + runner.trailing_args,
                                 description=runner.args.DESCRIPTION)
        else:
            catalog.create_alias(runner.args.ALIAS,
                                 [runner.args.COMMAND] + runner.trailing_args,
                                 description=runner.args.DESCRIPTION)


def _get_sanitized_aliases(runner: jiig.TaskRunner) -> Iterator[Alias]:
    with runner.open_alias_catalog() as catalog:
        for name in runner.args.ALIASES:
            alias = catalog.resolve_alias(name)
            if alias is not None:
                yield alias
            else:
                log_error(f'Alias "{name}" does not exist.')


@jiig.sub_task(task_alias,
               'show',
               jiig.argument('ALIASES',
                             description='Alias name(s) to display',
                             cardinality='+'),
               description='Display alias')
def task_alias_show(runner: jiig.TaskRunner):
    for line in _format_aliases(_get_sanitized_aliases(runner)):
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
