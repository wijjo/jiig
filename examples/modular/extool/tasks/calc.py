"""Sample Jiig task module."""

from jiig.task import task
from jiig.runtime import Runtime
from jiig import fields


@task
def calc(
    runtime: Runtime,
    blocks: fields.text(repeat=(1, None)),
):
    """
    evaluate formula using Python interpreter

    :param runtime: jiig runtime api
    :param blocks: formula block(s) to evaluate
    """
    try:
        result = eval(' '.join(blocks))
        runtime.message(f'The result is {result}.')
    except Exception as exc:
        runtime.abort(f'Formula error: {exc}')
