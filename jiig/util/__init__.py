"""
Jiig utility library.
"""

# Provide package access to all modules that have no unwanted external
# dependencies. This allows clients to use fully-specified package names, e.g.
# jiig.util.general in code.
from . import \
    alias_catalog, \
    console, \
    date_time, \
    filesystem, \
    footnotes, \
    general, \
    help_formatter, \
    init_file, \
    network, \
    process, \
    python, \
    stream, \
    template_expansion

from .options import Options
