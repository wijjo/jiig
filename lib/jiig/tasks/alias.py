"""
Alias sub-command tasks.
"""

from typing import Text, Iterator, Iterable, Optional, List

import jiig

from jiig.utility import alias_catalog
from jiig.utility.general import format_table
from jiig.utility.console import log_message, log_error


class AliasDeleteTask(jiig.Task):
    """Delete alias."""

    # For type inspection only.
    class Data:
        ALIAS: Text
    data: Data

    args = [
        jiig.Arg('ALIAS', 'Name of alias to delete.'),
    ]

    def on_run(self):
        with self.open_alias_catalog() as catalog:
            catalog.delete_alias(self.data.ALIAS)


class AliasDescriptionTask(jiig.Task):
    """Set alias description."""

    # For type inspection only.
    class Data:
        ALIAS: Text
        DESCRIPTION: Text
    data: Data

    args = [
        jiig.Arg('ALIAS', 'Target alias name for description.'),
        jiig.Arg('DESCRIPTION', 'Alias description.'),
    ]

    def on_run(self):
        with self.open_alias_catalog() as catalog:
            description_text = ' '.join(self.data.DESCRIPTION)
            catalog.update_alias(self.data.ALIAS, description=description_text)


class AliasListTask(jiig.Task):
    """List aliases."""

    # For type inspection only.
    class Data:
        EXPAND_NAMES: bool
    data: Data

    args = [
        jiig.BoolOpt(('-e', '--expand-names'), 'EXPAND_NAMES',
                     'Display expanded paths in names.'),
    ]

    def on_run(self):
        displayed_line_count = 0
        with self.open_alias_catalog() as catalog:
            for line in self._format_aliases(catalog.iterate_aliases(),
                                             long_names=self.data.EXPAND_NAMES):
                log_message(line)
                displayed_line_count += 1
        # _format_aliases() returns no lines, not even a heading, if no aliases exist.
        if displayed_line_count == 0:
            log_message('No aliases exist.')

    @staticmethod
    def _format_aliases(aliases: Iterable[alias_catalog.Alias],
                        long_names=False,
                        ) -> Iterator[Text]:
        # Keep alias labels grouped and sorted by path within the group.
        raw_rows = sorted([
            (iter_alias.name if long_names else iter_alias.short_name,
             iter_alias.description,
             iter_alias.command_string,
             iter_alias.label,
             (iter_alias.path if long_names else iter_alias.short_path) or '')
            for iter_alias in aliases
        ], key=lambda row: (row[3], row[4]))
        if raw_rows:
            rows = [row[:3] for row in raw_rows]
            for line in format_table(*rows, headers=['alias', 'description', 'command']):
                yield line


class AliasRenameTask(jiig.Task):
    """Rename alias."""

    # For type inspection only.
    class Data:
        ALIAS: Text
        ALIAS_NEW: Text
    data: Data

    args = [
        jiig.Arg('ALIAS', 'Existing alias name.'),
        jiig.Arg('ALIAS_NEW', 'New alias name.'),
    ]

    def on_run(self):
        with self.open_alias_catalog() as catalog:
            catalog.rename_alias(self.data.ALIAS, self.data.ALIAS_NEW)


class AliasSetTask(jiig.Task):
    """Create or update alias."""

    # For type inspection only.
    class Data:
        DESCRIPTION: Optional[Text]
        ALIAS: Text
        COMMAND: Text
    data: Data

    args = [
        jiig.Opt(('-d', '--description'), 'DESCRIPTION', 'New alias description.'),
        jiig.Arg('ALIAS', 'Name of alias to create or update.'),
        jiig.Arg('COMMAND', 'Command with options and arguments.'),
    ]

    # The command to alias is fed as unparsed trailing arguments.
    receive_trailing_arguments = True

    def on_run(self):
        with self.open_alias_catalog() as catalog:
            if catalog.resolve_alias(self.data.ALIAS):
                catalog.update_alias(self.data.ALIAS,
                                     command=[self.data.COMMAND] + self.trailing_arguments,
                                     description=self.data.DESCRIPTION)
            else:
                catalog.create_alias(self.data.ALIAS,
                                     [self.data.COMMAND] + self.trailing_arguments,
                                     description=self.data.DESCRIPTION)


class AliasShowTask(jiig.Task):
    """Display alias."""

    # For type inspection only.
    class Data:
        ALIASES: List[Text]
    data: Data

    args = [
        jiig.Arg('ALIASES', 'Alias name(s) to display.', cardinality='+'),
    ]

    def on_run(self):
        with self.open_alias_catalog() as catalog:
            for name in self.data.ALIASES:
                resolved_alias = catalog.resolve_alias(name)
                if resolved_alias is not None:
                    log_message(resolved_alias)
                else:
                    log_error(f'Alias "{name}" does not exist.')


class TaskClass(jiig.Task):
    """Alias management tasks."""

    sub_tasks = {
        'delete': AliasDeleteTask,
        'description': AliasDescriptionTask,
        'list': AliasListTask,
        'rename': AliasRenameTask,
        'set': AliasSetTask,
        'show': AliasShowTask,
    }

    def on_run(self):
        pass
