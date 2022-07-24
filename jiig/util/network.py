# Copyright (C) 2020-2022, Steven Cooper
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

"""Network utilities."""
import os
import re
from dataclasses import dataclass
from typing import Text, Optional
from urllib.error import URLError
from urllib.request import urlopen

from .log import abort
from .options import OPTIONS
from .process import run


@dataclass
class CurlResponse:
    text: Text
    status: int
    reason: Text


def curl(url: Text):
    """Download from a URL and return a CurlResponse object."""
    try:
        response = urlopen(url)
        return CurlResponse(
            response.read().decode('utf-8'),
            getattr(response, 'status', None),
            getattr(response, 'reason', None),
        )
    except URLError as exc:
        abort('cURL failed', url, exception=exc)


def resolve_ip_address(host: str) -> Optional[str]:
    if OPTIONS.dry_run:
        return '1.1.1.1'
    ip_extract_re = re.compile(rf'^PING {host} \((\d+\.\d+\.\d+\.\d+)\):')
    for line in run(['ping', '-c', '1', host], capture=True).stdout.split(os.linesep):
        result = ip_extract_re.search(line)
        if result:
            return result.group(1)
    return None


def format_host_string(host: str = None, user: str = None) -> Optional[str]:
    if not host:
        return None
    if not user:
        return host
    return f'{user}@{host}' if user else host
