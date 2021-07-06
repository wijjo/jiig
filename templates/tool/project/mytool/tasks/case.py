"""Sample Jiig task module."""

import jiig


@jiig.task
def case(
    runtime: jiig.Runtime,
    upper: jiig.f.boolean('convert to all-uppercase', cli_flags='-u'),
    lower: jiig.f.boolean('convert to all-lowercase', cli_flags='-l'),
    blocks: jiig.f.text('text block(s) to convert', repeat=(1, None)),
):
    """Convert text case (default is "smart" conversion)."""
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
