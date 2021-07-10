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
def calc(
    runtime: jiig.Runtime,
    blocks: jiig.f.text(repeat=(1, None)),
):
    """
    evaluate formula using Python interpreter

    :param runtime: jiig runtime api
    :param blocks: formula block(s) to evaluate
    """
    result = eval(' '.join(blocks))
    runtime.message(f'The result is {result}.')


@jiig.task(
    cli={
        'options': {
            'upper': ('-u', '--upper'),
            'lower': ('-l', '--lower'),
        }
    }
)
def case(
    runtime: jiig.Runtime,
    upper: jiig.f.boolean(),
    lower: jiig.f.boolean(),
    blocks: jiig.f.text(repeat=(1, None)),
):
    """
    convert text case (default is "smart" conversion)

    :param runtime: jiig runtime api
    :param upper: convert to all-uppercase
    :param lower: convert to all-lowercase
    :param blocks: text block(s) to convert
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


# noinspection PyUnusedLocal
@jiig.task(tasks=(case, words, calc))
def root(runtime: jiig.Runtime):
    """
    various text manipulations

    :param runtime: jiig runtime api
    """
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
