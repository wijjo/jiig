"""
Jiig task creation task root.
"""

import jiig

from . import create


class Task(jiig.Task,
           tasks={'create': create}
           ):
    """Manage task modules."""
    pass
