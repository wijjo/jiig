"""Sample Jiig words task module."""

from jiig import fields
from jiig.task import task
from jiig.runtime import Runtime


@task
def words(
    runtime: Runtime,
    blocks: fields.text(repeat=(1, None)),
):
    """
    count words using primitive whitespace splitting

    :param runtime: jiig runtime api
    :param blocks: text block(s) with words to count
    """
    count = len(' '.join(blocks).split())
    runtime.message(f'The word count is {count}.')
