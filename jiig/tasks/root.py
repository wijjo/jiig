"""
Jiig root task.
"""

import jiig

from . import alias, help, pdoc, task, tool, unittest, venv


class Task(jiig.Task,
           tasks={'task': task.root,
                  'tool': tool.root,
                  'venv': venv.root,
                  'alias[s]': alias.root,
                  'help[s]': help,
                  'pdoc[s]': pdoc.root,
                  'unittest[h]': unittest},
           ):
    pass
