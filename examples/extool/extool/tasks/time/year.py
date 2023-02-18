"""Sample Jiig time.year task module."""

import calendar
from datetime import datetime

from jiig.task import task
from jiig.runtime import Runtime
from jiig import fields


# noinspection PyUnusedLocal
@task
def _year(
    runtime: Runtime,
    year: fields.text() = None,
):
    """
    display current year

    :param runtime: jiig runtime api
    :param year: optional year override (2 or 4 digits)
    """
    if year is None:
        t = datetime.now()
    else:
        if len(year) == 2:
            year = f'20{year}'
        elif len(year) != 4:
            runtime.abort('bad year')
        t = datetime.fromisoformat(f'{year}-01-01')
    print(calendar.calendar(t.year))
