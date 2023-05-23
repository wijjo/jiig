"""Sample Jiig time.now task module."""

from datetime import datetime

from jiig.task import task
from jiig.runtime import Runtime
from jiig import fields


# noinspection PyUnusedLocal,PyShadowingBuiltins
@task
def now(
    runtime: Runtime,
    format: fields.text() = None,
):
    """
    display current date and time with overridable format

    Args:
        runtime: jiig runtime api
        format: optional format override
    """
    t = datetime.now()
    if format is None:
        print(t.isoformat())
    else:
        print(t.strftime(format))
