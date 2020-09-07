"""Network utilities."""

from dataclasses import dataclass
from typing import Text
from urllib.error import URLError
from urllib.request import urlopen

from .console import abort


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
