"""Sample Jiig task module."""

import jiig


@jiig.task
def words(
    runtime: jiig.Runtime,
    blocks: jiig.f.text('text block(s) with words to count', repeat=(1, None)),
):
    """Count words using primitive whitespace splitting."""
    count = len(' '.join(blocks).split())
    runtime.message(f'The word count is {count}.')
