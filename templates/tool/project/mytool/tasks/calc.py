"""Sample Jiig task module."""

import jiig


@jiig.task
def calc(
    runtime: jiig.Runtime,
    blocks: jiig.f.text('formula block(s) to evaluate', repeat=(1, None)),
):
    """Evaluate formula using Python interpreter."""
    result = eval(' '.join(blocks))
    runtime.message(f'The result is {result}.')
