"""
Runtime options passed to Tool and Task instances.
"""

from dataclasses import dataclass


@dataclass
class RuntimeOptions:
    """Runtime options."""
    debug: bool
    dry_run: bool
    verbose: bool
