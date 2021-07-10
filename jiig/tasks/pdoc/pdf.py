"""
Pdoc3 PDF documentation generation task.
"""

import jiig


# noinspection PyUnusedLocal
@jiig.task
def pdf(runtime: jiig.Runtime):
    """
    Use Pdoc3 to build PDF format documentation.

    :param runtime: Jiig runtime API.
    """
    raise NotImplementedError
