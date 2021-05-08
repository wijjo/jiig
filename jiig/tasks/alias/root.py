"""
Jiig alias root task.
"""

import jiig

from . import delete, description, list, rename, set, show


class Task(jiig.Task,
           tasks={'delete': delete,
                  'description': description,
                  'list': list,
                  'rename': rename,
                  'set': set,
                  'show': show},
           ):
    """Alias management tasks."""
    pass
