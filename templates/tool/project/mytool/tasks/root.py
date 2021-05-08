"""
Root task
"""

import jiig

from jiig.tasks import alias, help

from . import calc, case, words


class Task(jiig.Task,
           tasks={'calc': calc,
                  'case': case,
                  'words': words,
                  'alias[s]': alias.root,
                  'help[s]': help}
           ):
    """top level tasks"""
    pass
