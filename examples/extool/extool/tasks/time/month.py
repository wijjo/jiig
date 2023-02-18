"""Sample Jiig time.month task module."""

import calendar
from datetime import datetime

from jiig.task import task
from jiig.runtime import Runtime
from jiig import fields


# noinspection PyUnusedLocal
@task
def month(
    runtime: Runtime,
    date: fields.text() = None,
):
    """
    display current month

    Supports abbreviated ISO date strings, "month" and "year-month".

    Also supports 1 digit months and 2 digit years.

    :param runtime: jiig runtime api
    :param date: optional date (string) override
    """
    if date is None:
        t = datetime.now()
    else:
        try:
            now = datetime.now()
            parts = date.split('-')
            if len(parts) == 1:
                date = f'{now.year}-{int(parts[0]):02d}-01'
            elif len(parts) == 2:
                if len(parts[0]) not in (2, 4):
                    raise ValueError
                if len(parts[0]) == 2:
                    parts[0] = f'20{parts[0]}'
                date = f'{parts[0]}-{int(parts[1]):02d}-01'
            t = datetime.fromisoformat(date)
        except ValueError:
            runtime.abort(f'bad ISO date string')
    print(calendar.month(t.year, t.month))
