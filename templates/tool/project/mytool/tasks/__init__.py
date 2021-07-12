import jiig

from . import task_imports          # noqa


@jiig.task(tasks=task_references)   # noqa
def root(runtime: jiig.Runtime):    # noqa
    """
    top level tasks

    :param runtime: jiig runtime api
    """
    pass
