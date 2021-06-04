"""
Git-related utilities.
"""


def repo_name_from_url(url: str) -> str:
    return url.split('.')[-2].split('/')[-1]

