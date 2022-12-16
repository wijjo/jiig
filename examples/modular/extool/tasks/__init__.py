from jiig.task import task
from jiig.runtime import Runtime

from . import calc, case, words


# noinspection PyUnusedLocal
@task(tasks=(calc, case, words))
def root(runtime: Runtime):
    """
    top level tasks

    :param runtime: jiig runtime api
    """
    pass
