"""Jiig pdoc sub-task imports."""

import jiig

from . import html, pdf, server


@jiig.task(
    tasks={
        'html': html,
        'pdf': pdf,
        'server': server,
    },
)
def root(_runtime: jiig.Runtime):
    """Pdoc3 documentation tasks."""
    pass
