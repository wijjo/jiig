#!/usr/bin/env python3
"""
mytool (jiig monolithic tool script - pure-Python version).

PYTHONPATH (i.e. sys.path) must include Jiig lib for `import jiig` to work.

To use a virtual environment, either let `jiig.main()` automatically create and
restart in it or activate the virtual environment prior to running this script.
"""

import os
import sys

# Add Jiig root to Python path so that Jiig modules can be loaded.
# Alternatively, can use PYTHONPATH or any other supported mechanism for
# extending the library load path.
sys.path.insert(0, 'jiig_root')

import jiig     # noqa: E402


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


@jiig.task
def words(
    runtime: jiig.Runtime,
    blocks: jiig.f.text('text block(s) with words to count', repeat=(1, None)),
):
    """Count words using primitive whitespace splitting."""
    count = len(' '.join(blocks).split())
    runtime.message(f'The word count is {count}.')


@jiig.task
def calc(
    runtime: jiig.Runtime,
    blocks: jiig.f.text('formula block(s) to evaluate', repeat=(1, None)),
):
    """Evaluate formula using Python interpreter."""
    result = eval(' '.join(blocks))
    runtime.message(f'The result is {result}.')


@jiig.task(tasks=(case, words, calc))
def root(_runtime: jiig.Runtime):
    """Various text manipulations."""
    pass


TOOL = jiig.Tool(
    tool_name='mytool',
    tool_root_folder=os.path.dirname(__file__),
    description='mytool description.',
    root_task=root,
    # driver='jiig.driver.cli',
    # driver_variant='argparse',
    # pip_packages=[],
    # options=jiig.ToolOptions(),
)


if __name__ == '__main__':
    jiig.main(TOOL)
