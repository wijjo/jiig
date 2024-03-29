"""Sample Jiig calc task module."""

from jiig import fields
from jiig.task import task
from jiig.runtime import Runtime


@task
def case(
    runtime: Runtime,
    upper: fields.boolean(),
    lower: fields.boolean(),
    blocks: fields.text(repeat=(1, None)),
):
    """
    convert text case (default is "smart" conversion)

    Args:
        runtime: jiig runtime api
        upper: convert to all-uppercase
        lower: convert to all-lowercase
        blocks: text block(s) to convert
    """
    if upper and lower:
        raise RuntimeError('Conflicting upper/lower options specified.')
    if not upper and not lower:
        # "Smart" conversion checks first character of first block.
        to_upper = blocks[0][:1].islower()
    else:
        to_upper = upper
    text = ' '.join(blocks)
    if to_upper:
        output_text = text.upper()
    else:
        output_text = text.lower()
    runtime.message(output_text)
