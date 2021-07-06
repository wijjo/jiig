"""
Jiig utility library.
"""

# Provide package access to all modules that have no unwanted external
# dependencies. This allows clients to use fully-specified package names, e.g.
# jiig.util.general in code. The `gui` sub-package is an example of one that
# must be excluded due to its dependency on PySimpleGUI.
from . import \
    alias_catalog, \
    log, \
    date_time, \
    filesystem, \
    footnotes, \
    general, \
    help_formatter, \
    init_file, \
    network, \
    options, \
    process, \
    python, \
    repetition, \
    scanners, \
    stream, \
    template_expansion


from .options import OPTIONS
