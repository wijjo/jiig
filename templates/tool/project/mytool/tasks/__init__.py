import jiig

from . import calc, case, words


class Task(
    jiig.Task,
    tasks={
        'calc': calc,
        'case': case,
        'words': words,
        'alias[s]': jiig.tasks.alias,
        'help[s]': jiig.tasks.help,
    }
):
    """top level tasks"""
    pass
