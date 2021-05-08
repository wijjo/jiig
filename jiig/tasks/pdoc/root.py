"""
Pdoc3 root task.
"""

import jiig

from . import html, pdf, server


class Task(jiig.Task,
           tasks={'html': html,
                  'pdf': pdf,
                  'server': server},
           ):
    """Pdoc3 documentation tasks."""
    pass
