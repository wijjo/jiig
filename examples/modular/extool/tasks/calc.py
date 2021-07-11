"""Sample Jiig task module."""

import jiig


@jiig.task
def calc(
    runtime: jiig.Runtime,
    blocks: jiig.f.text(repeat=(1, None)),
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
