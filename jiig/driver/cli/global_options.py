"""
Supported global CLI options.
"""

from dataclasses import dataclass
from typing import List, Sequence, Text


@dataclass
class GlobalOption:
    name: str
    flags: Sequence[Text]
    description: str

    @property
    def dest(self) -> Text:
        return self.name.upper()


GLOBAL_OPTIONS: List[GlobalOption] = [
    GlobalOption('debug', ['--debug'], 'enable debug mode for additional diagnostics'),
    GlobalOption('dry_run', ['--dry-run'], 'display actions without executing them (dry run)'),
    GlobalOption('verbose', ['-v', '--verbose'], 'display additional (verbose) messages'),
    GlobalOption('pause', ['--pause'], 'pause before significant activity'),
    GlobalOption('keep_files', ['--keep-files'], 'keep (do not delete) temporary files'),
]
