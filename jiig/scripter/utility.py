import os
from subprocess import run
from typing import List, Optional


def make_list(item_or_seq) -> list:
    if isinstance(item_or_seq, list):
        return item_or_seq
    if isinstance(item_or_seq, tuple):
        return list(item_or_seq)
    return [item_or_seq]


def repo_name_from_url(url: str) -> str:
    return url.split('.')[-2].split('/')[-1]


class BlockSplitter:
    def __init__(self, *blocks: str, indent: int = None, double_spaced: bool = False):
        self.lines: List[str] = []
        self.indent = indent
        self.double_spaced = double_spaced
        self.found_indent: Optional[int] = None
        self._trimmed_lines: Optional[List[str]] = None
        for block in blocks:
            self.add_block(block)

    def add_block(self, block: str):
        if self.lines and self.double_spaced:
            self.lines.append('')
        have_empty = False
        have_non_empty = False
        for line in block.split(os.linesep):
            line = line.rstrip()
            line_length = len(line)
            indent = line_length - len(line.lstrip())
            if indent == line_length:
                have_empty = have_non_empty
            else:
                have_non_empty = True
                if have_empty:
                    self.lines.append('')
                    have_empty = False
                self.lines.append(line)
                if self.found_indent is None or indent < self.found_indent:
                    self.found_indent = indent

    @property
    def trimmed_lines(self) -> List[str]:
        indent = ' ' * self.indent if self.indent else ''
        if self._trimmed_lines is None:
            if self.found_indent:
                self._trimmed_lines = [indent + line[self.found_indent:] for line in self.lines]
            else:
                self._trimmed_lines = [indent + line for line in self.lines]
        return self._trimmed_lines


def trim_text_blocks(*blocks: str,
                     indent: int = None,
                     keep_indent: bool = False,
                     double_spaced: bool = False,
                     ) -> List[str]:
    splitter = BlockSplitter(*blocks, indent=indent, double_spaced=double_spaced)
    if keep_indent:
        return splitter.lines
    return splitter.trimmed_lines


def trim_text_block(block: str,
                    indent: int = None,
                    keep_indent: bool = False,
                    double_spaced: bool = False,
                    ) -> str:
    return os.linesep.join(trim_text_blocks(block,
                                            indent=indent,
                                            keep_indent=keep_indent,
                                            double_spaced=double_spaced))


def get_client_name() -> str:
    client = run('uname -n', shell=True, capture_output=True, encoding='utf-8').stdout.strip()
    if client.endswith('.local_command'):
        client = client[:-6]
    return client
