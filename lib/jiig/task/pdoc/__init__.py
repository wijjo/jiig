"""
Pdoc3 root task.
"""

__all__ = ['html', 'pdf', 'server']

import jiig

from . import html, pdf, server


TASK = jiig.Task(
    description='Pdoc3 documentation tasks.',
    tasks={
        'html': html,
        'pdf': pdf,
        'server': server,
    },
)
