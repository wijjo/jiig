import jiig

from . import calc, case, words


# noinspection PyUnusedLocal
@jiig.task(tasks=(calc, case, words))
def root(runtime: jiig.Runtime):
    """
    top level tasks

    :param runtime: jiig runtime api
    """
    pass
