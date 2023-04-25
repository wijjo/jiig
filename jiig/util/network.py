# Copyright (C) 2020-2023, Steven Cooper
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
from typing import Any, Hashable, Callable
from urllib.error import URLError
from urllib.request import urlopen, Request

from .collections import AttributeDictionary
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
    """Download from a URL and return a CurlResponse object.

    Args:
        url: URL to access

    Returns:
        response data
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


def format_host_string(host: str = None, user: str = None) -> str | None:
    if not host:
        return None
    if not user:
        return host
    return f'{user}@{host}' if user else host


def split_host_string(host_string: str) -> tuple[str, str]:
    """Split host string into host/user pair.

    Provides local user if missing.

    Args:
        host_string: host string as "user@host" or just "host"

    Returns:
        (host_name, user_name) tuple
    """
    if not host_string:
        return '', ''
    host_fields = host_string.split('@', maxsplit=1)
    if len(host_fields) == 1:
        return host_fields[0], os.environ['USER']
    return host_fields[1], host_fields[0]


def full_host_string(host_string: str) -> str:
    """Replace missing user in user@host with USER environment variable.

    Args:
        host_string: host string as "user@host" or just "host"

    Returns:
        host string with missing user provided
    """
    user, host = split_host_string(host_string)
    return f'{user}@{host}'


def download_text(url_or_request: str | Request,
                  headers: dict = None,
                  timeout: float = None,
                  unchecked: bool = False,
                  ) -> str:
    """Download text from URL.

    Aborts on any failure.

    Args:
        url_or_request: target URL or Request object
        headers: optional HTML headers
        timeout: timeout in seconds
        unchecked: pass along exceptions if True, otherwise abort

    Returns:
        downloaded text
    """
    try:
        kwargs = {}
        if headers:
            kwargs['headers'] = headers
        if isinstance(url_or_request, Request):
            request = url_or_request
            if headers:
                request.headers.update(headers)
        else:
            request = Request(url_or_request, **kwargs)
        response = urlopen(request, timeout=timeout)
        raw_data = response.read()
        if isinstance(raw_data, str):
            return raw_data.rstrip()
        return raw_data.decode('utf-8').rstrip()
    except URLError as exc:
        if not unchecked:
            abort(f'Failed to download URL: {url_or_request}', exc)
        raise


def download_json(url_or_request: str | Request,
                  headers: dict = None,
                  timeout: float = None,
                  ) -> AttributeDictionary:
    """Download JSON data from URL.

    Args:
        url_or_request: target URL or Request object
        headers: optional headers
        timeout: timeout in seconds

    Returns:
        downloaded and decoded JSON data
    """
    try:
        json_text = download_text(url_or_request, headers=headers, timeout=timeout)
        json_data = json.loads(json_text)
        if isinstance(json_data, list):
            # A little hack-y, but does leverage attribute_dictionary() for a list.
            return AttributeDictionary.new({'wrapped': json_data}).wrapped
        return AttributeDictionary.new(json_data)
    except json.JSONDecodeError as exc:
        abort(f'Failed to parse JSON data from URL: {url_or_request}', exc)


def get_client_name() -> str:
    """Get client system name.

    Returns:
        client name
    """
    client = pipe(['uname', '-n'])[0]
    if client.endswith('.local'):
        client = client[:-6]
    return client


def ssh_key_works(host: str) -> bool:
    """Check if SSH key works for password-less access to host.

    Args:
        host: host string

    Returns:
        True if the SSH key works
    """
    return run(['ssh', host, '-o', 'PasswordAuthentication=no', 'true'],
               unchecked=True).returncode == 0


def resolve_ip_address(host: str, checked: bool = False) -> str | None:
    """Resolve IP address for host.

    Caches IP addresses to minimize repeat call latency.

    Args:
        host: host name
        checked: abort if unable to get IP address

    Returns:
        ip address or None if the host is inaccessible
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
    """Check if host is alive.

    Args:
        host_or_ip: host name or IP address

    Returns:
        True if the host is alive
    """
    return run(['ping', '-q', '-t', '2', '-c', '1', host_or_ip], capture=True,
               unchecked=True).returncode == 0


def is_ip_address(possible_ip_addr: str) -> bool:
    """Check if string looks like an IP address.

    Args:
        possible_ip_addr: string to check for matching IP address pattern

    Returns:
        True if it looks like an IP address
    """
    return bool(IP_ADDRESS_REGEX.match(possible_ip_addr))


class NoStateCls:
    """Class for special NoState instance."""
    pass


NoState = NoStateCls()


class ElementScanner:
    """HTML element scanner."""

    def __init__(self,
                 tag: str,
                 style_classes: set[str],
                 text_pattern: re.Pattern,
                 function: Callable):
        """
        HTML element scanner constructor.

        :param tag: case-insensitive tag literal for filtering elements
        :param style_classes: style class regex patterns
        :param text_pattern: regular expression for searching the inner text block
        :param function: callback function
        """
        self.tag = tag
        self.style_classes = style_classes
        self.text_pattern = text_pattern
        self.function = function


class HTMLScanner:
    """Base class for awk-like web HTML scanners."""

    scanners: dict[Any, list[ElementScanner]] = None

    def __init__(self):
        """HTML scanner constructor."""
        self._state = None

    @classmethod
    def match(cls,
              tag: str = None,
              style_class: str = None,
              text: str = None,
              state: Any = None):
        """Decorator for methods that participate in HTML scanning and extraction.

        Args:
            tag: case-insensitive tag literal for filtering elements
            style_class: style class regex patterns
            text: regular expression for searching the inner text block
            state: required state if set, or all states if not
        """
        if cls.scanners is None:
            cls.scanners = {}

        def _inner(function: Callable) -> Callable:
            element_scanner = ElementScanner(
                tag,
                set(style_class.split()),
                re.compile(text),
                function)
            cls.scanners.setdefault(state, []).append(element_scanner)
            return function

        return _inner

    def _call_line_handlers(self, line: str, state: Any | None) -> bool:
        for matcher, handler in self.scanners.get(state, []):
            match = matcher.match(line)
            if match:
                handler(self, match)
        # TODO
        return False

    def scan(self,
             url_or_request: str | Request,
             headers: dict = None,
             timeout: float = None,
             state: Any = NoState,
             ):
        """Scan an HTML string, file, stream, or URL.

        Args:
            url_or_request: HTML input URL or Request object
            headers: optional HTML headers
            timeout: timeout in seconds when downloading URL or Request
            state: next state value

        Returns:
            self for chaining
        """
        text = download_text(url_or_request, headers=headers, timeout=timeout)
        if state is not NoState:
            self.set_state(state)
        self.begin()
        try:
            for line in text.split(os.linesep):
                for matcher, handler in self.scanners.get(self._state, []):
                    match = matcher.match(line)
                    if match:
                        handler(self, match)
        except StopIteration:
            pass
        # Make it chainable for one-liners.
        return self

    def end_scan(self):
        """Call to end in-progress scan."""
        raise StopIteration

    def begin(self, *args, **kwargs):
        """Begin scan.

        Args:
            *args: positional arguments
            **kwargs: keyword arguments
        """
        pass

    def get_state(self) -> Hashable:
        """Get scan state.

        Returns:
            state
        """
        return self._state

    def set_state(self, state: Hashable):
        """Set state.

        Args:
            state: state
        """
        if state not in self.scanners:
            raise RuntimeError(f'State {state} is not supported by '
                               f'parser: {self.__class__.__name__}')
        self._state = state
