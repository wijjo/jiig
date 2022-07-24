# Copyright (C) 2021-2022, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

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
