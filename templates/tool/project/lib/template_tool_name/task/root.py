"""
Root task
"""

import jiig
from jiig.task import alias, help

from . import template_task_name

TASK = jiig.Task(
    tasks={
        'template_task_name': template_task_name,
        'alias[s]': alias,
        'help[s]': help,
    },
)
