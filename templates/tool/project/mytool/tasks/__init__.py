import jiig

from . import calc, case, words


@jiig.task(tasks=(calc, case, words))
def root(_runtime: jiig.Runtime):
    """top level tasks"""
    pass
