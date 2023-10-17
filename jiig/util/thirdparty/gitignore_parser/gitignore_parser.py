"""
Gitignore parsing.

https://github.com/mherrmann/gitignore_parser/blob/master/gitignore_parser.py

Jiig tweaks:
- Fix bugs.
- Eliminate type inspection errors.
- Improve and modernize type specifications.
- Add doc strings.
"""

import os
import re

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Callable

# Matches "**" recursive fnmatch pattern expressions.
REGEX_RECURSIVE = re.compile(r'\*\*')


# Internal named tuple for a gitignore pattern rule.
@dataclass
class _IgnoreRule:
    # Basic values
    pattern: str
    regex: re.Pattern
    # Behavior flags
    negation: bool
    directory_only: bool
    anchored: bool
    # Meaningful for gitignore-style behavior
    base_path: Path
    # (file, line) tuple for reporting
    source: tuple[Path, int]

    def __str__(self):
        return self.pattern

    def __repr__(self):
        return ''.join(['_IgnoreRule(\'', self.pattern, '\')'])

    def match(self, abs_path: str | Path):
        matched = False
        if self.base_path:
            # SC rel_path = str(Path(abs_path).resolve().relative_to(self.base_path))
            rel_path = str(Path(abs_path).absolute().relative_to(self.base_path))
        else:
            rel_path = str(Path(abs_path))
        # Path() strips the trailing slash, so we need to preserve it
        # in case of directory-only negation
        if self.negation and type(abs_path) is str and abs_path[-1] == '/':
            rel_path += '/'
        if rel_path.startswith('./'):
            rel_path = rel_path[2:]
        if self.regex.search(rel_path):
            matched = True
        return matched


class GitignoreMatcher:
    """Callable class to match file path patterns."""

    def __init__(self,
                 full_path: str | Path,
                 base_dir: str | Path | None,
                 ):
        """
        GitignoreMatcher constructor.

        :param full_path: gitignore file full path
        :param base_dir: base directory for file path pattern matching
        """
        self.full_path = Path(full_path)
        if base_dir is None:
            base_dir = self.full_path.parent
        self.base_path = Path(base_dir).resolve()
        self.rules: list[_IgnoreRule] = []
        self.counter = 0
        self.has_negation = False

    def add_pattern(self, pattern: str):
        """
        Add pattern to rules.

        :param pattern: pattern to add
        """
        self.counter += 1
        rule = self._rule_from_pattern(pattern)
        if rule:
            if rule.negation:
                self.has_negation = True
            self.rules.append(rule)

    def __call__(self, path: str | Path,
                 ) -> bool:
        """
        Check if path matches any rule.

        :param path: path to match against rules
        :return: True if path matches
        """
        # Use any(...) for efficiency if no negation is present.
        if not self.has_negation:
            return any(rule.match(str(path)) for rule in self.rules)
        # Otherwise perform matching without using any(...).
        for rule in self.rules:
            if rule.match(path):
                if not rule.negation:
                    return True
            elif rule.negation:
                return True
        return False

    def _rule_from_pattern(self,
                           pattern: str,
                           ) -> _IgnoreRule | None:
        """
        Take a .gitignore match pattern, such as "*.py[cod]" or "**/*.bak",
        and return an _IgnoreRule suitable for matching against files and
        directories. Patterns which do not match files, such as comments
        and blank lines, will return None.
        Because git allows for nested .gitignore files, base_path is required
        for correct behavior, and base_path must be absolute.
        """
        # Store the exact pattern for our repr and string functions
        orig_pattern = pattern
        # Early returns follow
        # Discard comments and separators
        if pattern.strip() == '' or pattern[0] == '#':
            return
        # Discard anything with more than two consecutive asterisks
        if pattern.find('***') > -1:
            return
        # Strip leading bang before examining double asterisks
        if pattern[0] == '!':
            negation = True
            pattern = pattern[1:]
        else:
            negation = False
        # Discard anything with invalid double-asterisks -- they can appear
        # at the start or the end, or be surrounded by slashes
        for m in REGEX_RECURSIVE.finditer(pattern):
            start_index = m.start()
            if (start_index != 0 and start_index != len(pattern) - 2 and
                    (pattern[start_index - 1] != '/' or
                     pattern[start_index + 2] != '/')):
                return

        # Special-casing '/', which doesn't match any files or directories
        if pattern.rstrip() == '/':
            return

        directory_only = pattern[-1] == '/'
        # A slash is a sign that we're tied to the base_path of our rule
        # set.
        anchored = '/' in pattern[:-1]
        if pattern[0] == '/':
            pattern = pattern[1:]
        if pattern[0] == '*' and len(pattern) >= 2 and pattern[1] == '*':
            pattern = pattern[2:]
            anchored = False
        if pattern[0] == '/':
            pattern = pattern[1:]
        if pattern[-1] == '/':
            pattern = pattern[:-1]
        # patterns with leading hashes are escaped with a backslash in front, unescape it
        if pattern[0] == '\\' and pattern[1] == '#':
            pattern = pattern[1:]
        # trailing spaces are ignored unless they are escaped with a backslash
        i = len(pattern) - 1
        strip_trailing_spaces = True
        while i > 1 and pattern[i] == ' ':
            if pattern[i - 1] == '\\':
                pattern = pattern[:i - 1] + pattern[i:]
                i = i - 1
                strip_trailing_spaces = False
            else:
                if strip_trailing_spaces:
                    pattern = pattern[:i]
            i = i - 1
        conversion = fnmatch_to_regex(pattern, directory_only, negation, anchored)
        if conversion.error:
            raise ValueError(': '.join([
                'gitignore_parser',
                'regular expression error',
                f're.error="{conversion.error}"',
                f'fnmatch="{conversion.fnmatch_pattern}"',
                f'regex="{conversion.regex_pattern}"',
            ]))
        return _IgnoreRule(
            pattern=orig_pattern,
            regex=conversion.regex_compiled,
            negation=negation,
            directory_only=directory_only,
            anchored=anchored,
            base_path=self.base_path,
            source=(self.full_path, self.counter)
        )


def parse_gitignore_file(full_path: str | Path,
                         base_dir: str | Path = None,
                         ) -> Callable[[str | Path], bool]:
    """
    Parse gitignore file and generate matching function.

    :param full_path: gitignore file path
    :param base_dir: base directory for file path pattern matching
    :return: matching function
    """
    matcher = GitignoreMatcher(full_path, base_dir)
    with open(full_path) as ignore_file:
        for line in ignore_file:
            matcher.add_pattern(line.rstrip(os.linesep))
    return matcher


def parse_gitignore_patterns(patterns: Sequence[str],
                             base_dir: str | Path,
                             ) -> Callable[[str | Path], bool]:
    """
    Parse pattern strings.

    :param patterns: gitignore-style pattern strings
    :param base_dir: base directory for applying rules
    :return: matching function
    """
    matcher = GitignoreMatcher('(patterns)', base_dir)
    for pattern in patterns:
        matcher.add_pattern(pattern)
    return matcher


@dataclass
class FNMatchToRegexResult:
    """fnmatch_to_regex result data."""
    fnmatch_pattern: str
    regex_pattern: str
    regex_compiled: re.Pattern = None
    error: re.error = None


def fnmatch_to_regex(fnmatch_pattern: str,
                     directory_only: bool,
                     negation: bool,
                     anchored: bool,
                     ) -> FNMatchToRegexResult:
    """
    Convert fnmatch-style pattern to regular expression.

    Works as if FNM_PATHNAME is enabled. Frustratingly, python's fnmatch doesn't
    provide the FNM_PATHNAME option that .gitignore's behavior depends on.

    The path separator deos not match shell-style '*' and '.' wildcards.

    :param fnmatch_pattern: fnmatch pattern string
    :param directory_only: match directory only if True
    :param negation: negate the pattern
    :param anchored: anchor to start of string
    :return FNMatchToRegexResult: result data, including possible compilation error
    """
    i, n = 0, len(fnmatch_pattern)

    separators = [re.escape(os.sep)]
    if os.altsep is not None:
        separators.append(re.escape(os.altsep))
    separators_group = '[' + '|'.join(separators) + ']'
    non_separator = r'[^{}]'.format('|'.join(separators))

    regexes = []
    if anchored:
        regexes.append('^')
    while i < n:
        c = fnmatch_pattern[i]
        i += 1
        if c == '*':
            try:
                if fnmatch_pattern[i] == '*':
                    i += 1
                    regexes.append('.*')
                    if fnmatch_pattern[i] == '/':
                        i += 1
                        regexes.append(''.join([separators_group, '?']))
                else:
                    regexes.append(''.join([non_separator, '*']))
            except IndexError:
                regexes.append(''.join([non_separator, '*']))
        elif c == '?':
            regexes.append(non_separator)
        elif c == '/':
            regexes.append(separators_group)
        elif c == '[':
            j = i
            if j < n and fnmatch_pattern[j] == '!':
                j += 1
            if j < n and fnmatch_pattern[j] == ']':
                j += 1
            while j < n and fnmatch_pattern[j] != ']':
                j += 1
            if j >= n:
                regexes.append('\\[')
            else:
                stuff = fnmatch_pattern[i:j].replace('\\', '\\\\')
                i = j + 1
                if stuff[0] == '!':
                    stuff = ''.join(['^', stuff[1:]])
                elif stuff[0] == '^':
                    stuff = ''.join('\\' + stuff)
                regexes.append('[{}]'.format(stuff))
        else:
            regexes.append(re.escape(c))
    regexes.insert(0, '(?ms)')
    if not directory_only:
        regexes.append('$')
    if directory_only and negation:
        regexes.append('/$')
    regex_pattern = ''.join(regexes)
    result = FNMatchToRegexResult(fnmatch_pattern, regex_pattern)
    try:
        result.regex_compiled = re.compile(result.regex_pattern)
    except re.error as exc:
        result.error = exc
    return result
