# Copyright (C) 2023, Steven Cooper
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

"""Build source distribution."""

import json

import jiig
from jiig.util.configuration import read_toml_configuration


def _read_toml_configuration(runtime: jiig.Runtime, config_path: str) -> dict:
    try:
        return read_toml_configuration(config_path)
    except TypeError as type_exc:
        runtime.abort(str(type_exc))
    except ValueError as value_exc:
        runtime.abort(str(value_exc))
    except (IOError, OSError) as file_exc:
        runtime.abort(f'Failed to read TOML configuration file.',
                      path=config_path,
                      exception=file_exc)


@jiig.task
def toml_to_json(
    runtime: jiig.Runtime,
    source: jiig.f.filesystem_file(),
    target: jiig.f.filesystem_object(),
):
    """Convert configuration file format.

    Args:
        runtime: Jiig runtime API.
        source: Source TOML format configuration file.
        target: Target JSON format configuration file.
    """
    data = _read_toml_configuration(runtime, source)
    try:
        with open(target, 'w', encoding='utf-8') as target_file:
            json.dump(data, target_file, indent=2)
            runtime.message(f'JSON configuration saved: {target}')
    except (IOError, OSError) as file_exc:
        runtime.abort(f'Failed to write JSON configuration file.',
                      path=target_file,
                      exception=file_exc)
