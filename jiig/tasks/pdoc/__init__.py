"""Jiig pdoc sub-task imports."""

import jiig

from . import html, pdf, server


# noinspection PyUnusedLocal
@jiig.task(tasks=(html, pdf, server))
def root(runtime: jiig.Runtime):
    """
    Pdoc3 documentation tasks.

    :param runtime: Jiig runtime API.
    """
    pass
