"""
Root task
"""

import jiig

from . import mytask

TASK = jiig.Task(
    tasks={
        'mytask': mytask,
        'alias[s]': jiig.task.alias,
        'help[s]': jiig.task.help,
    },
)
