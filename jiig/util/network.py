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
import json
import os
import re
from dataclasses import dataclass
from typing import Tuple, Optional
from urllib.error import URLError
from urllib.request import urlopen, Request

from .json import JSONDict
from .log import abort
from .options import OPTIONS
from .process import run, pipe

IP_ADDRESS_PATTERN = r'\d+\.\d+\.\d+\.\d+'
IP_ADDRESS_REGEX = re.compile(rf'^{IP_ADDRESS_PATTERN}$')
IP_ADDRESS_CACHE: dict[str, str] = {}


@dataclass
class CurlResponse:
    text: str
    status: int
    reason: str


def curl(url: str) -> CurlResponse:
    """
    Download from a URL and return a CurlResponse object.

    :param url: URL to access
    :return: response data
    """
    try:
        response = urlopen(url)
        return CurlResponse(
            response.read().decode('utf-8'),
            getattr(response, 'status', None),
            getattr(response, 'reason', None),
        )
    except URLError as exc:
        abort('cURL failed', url, exception=exc)


def format_host_string(host: str = None, user: str = None) -> Optional[str]:
    if not host:
        return None
    if not user:
        return host
    return f'{user}@{host}' if user else host


def split_host_string(host_string: str) -> Tuple[str, str]:
    """
    Split host string into host/user pair.

    Provides local user if missing.

    :param host_string: host string as "user@host" or just "host"
    :return: (host_name, user_name) tuple
    """
    if not host_string:
        return '', ''
    host_fields = host_string.split('@', maxsplit=1)
    if len(host_fields) == 1:
        return host_fields[0], os.environ['USER']
    return host_fields[1], host_fields[0]


def full_host_string(host_string: str) -> str:
    """
    Replace missing user in user@host with USER environment variable.

    :param host_string: host string as "user@host" or just "host"
    :return: host string with missing user provided
    """
    user, host = split_host_string(host_string)
    return f'{user}@{host}'


def download_text(url: str, headers: dict = None) -> str:
    """
    Download text from URL.

    Aborts on any failure.

    :param url: target URL
    :param headers: optional headers
    :return: downloaded text
    """
    try:
        kwargs = {}
        if headers:
            kwargs['headers'] = headers
        request = Request(url, **kwargs)
        response = urlopen(request)
        raw_data = response.read()
        if isinstance(raw_data, str):
            return raw_data.rstrip()
        return raw_data.decode('utf-8').rstrip()
    except URLError as exc:
        abort(f'Failed to download URL: {url}', exc)


def download_json(url: str, headers: dict = None) -> JSONDict:
    """
    Download JSON data from URL.

    :param url:
    :param headers: optional headers
    :return: downloaded and decoded JSON data
    """
    try:
        return JSONDict(json.loads(download_text(url, headers=headers)))
    except json.JSONDecodeError as exc:
        abort(f'Failed to parse JSON data from URL: {url}', exc)


def get_client_name() -> str:
    """
    Get client system name.

    :return: client name
    """
    client = pipe(['uname', '-n'])[0]
    if client.endswith('.local'):
        client = client[:-6]
    return client


def ssh_key_works(host: str) -> bool:
    """
    Check if SSH key works for password-less access to host.

    :param host: host string
    :return: True if the SSH key works
    """
    return run(['ssh', host, '-o', 'PasswordAuthentication=no', 'true'],
               unchecked=True).returncode == 0


def resolve_ip_address(host: str, checked: bool = False) -> Optional[str]:
    """
    Resolve IP address for host.

    Caches IP addresses to minimize repeat call latency.

    :param host: host name
    :param checked: abort if unable to get IP address
    :return: ip address or None if the host is inaccessible
    """
    if OPTIONS.dry_run:
        return '1.1.1.1'
    host_name, _user_name = split_host_string(host)
    if host_name in IP_ADDRESS_CACHE:
        return IP_ADDRESS_CACHE[host_name]
    ip_extract_re = re.compile(rf'^PING {host_name} \(({IP_ADDRESS_PATTERN})\):')
    for line in pipe(['ping', '-c', '1', host_name]):
        result = ip_extract_re.search(line)
        if result:
            ip_address = result.group(1)
            IP_ADDRESS_CACHE[host_name] = ip_address
            return ip_address
    if checked:
        abort(f'Failed to resolve IP address for host: {host}')
    return None


def is_host_alive(host_or_ip: str) -> bool:
    """
    Check if host is alive.

    :param host_or_ip: host name or IP address
    :return: True if the host is alive
    """
    return run(['ping', '-q', '-t', '2', '-c', '1', host_or_ip], capture=True,
               unchecked=True).returncode == 0


def is_ip_address(possible_ip_addr: str) -> bool:
    """
    Check if string looks like an IP address.

    :param possible_ip_addr: string to check for matching IP address pattern
    :return: True if it looks like an IP address
    """
    return bool(IP_ADDRESS_REGEX.match(possible_ip_addr))
