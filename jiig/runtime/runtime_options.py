"""
Jiig runtime options.
"""

from dataclasses import dataclass


@dataclass
class RuntimeOptions:
    debug: bool
    dry_run: bool
    verbose: bool
    pause: bool
