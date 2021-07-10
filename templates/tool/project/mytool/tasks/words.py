"""Sample Jiig task module."""

import jiig


@jiig.task
def words(
    runtime: jiig.Runtime,
    blocks: jiig.f.text(repeat=(1, None)),
):
    """
    count words using primitive whitespace splitting

    :param runtime: jiig runtime api
    :param blocks: text block(s) with words to count
    """
    count = len(' '.join(blocks).split())
    runtime.message(f'The word count is {count}.')
