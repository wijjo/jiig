"""
Alias list task.
"""

from typing import Text, Iterable, Iterator

import jiig
from jiig.util.alias_catalog import Alias
from jiig.util.console import log_message
from jiig.util.general import format_table


TASK = jiig.Task(
    description='List aliases.',
    args={
        'EXPAND_NAMES[!]': ('-e', '--expand-names', 'Display expanded paths in names.'),
    },
)


# For type inspection only.
class Data:
    EXPAND_NAMES: bool


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    displayed_line_count = 0
    with runner.open_alias_catalog() as catalog:
        for line in _format_aliases(catalog.iterate_aliases(), long_names=data.EXPAND_NAMES):
            log_message(line)
            displayed_line_count += 1
    # _format_aliases() returns no lines, not even a heading, if no aliases exist.
    if displayed_line_count == 0:
        log_message('No aliases exist.')


def _format_aliases(aliases: Iterable[Alias],
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
