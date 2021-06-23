"""Sample Jiig task module."""

import jiig


class TaskCase(jiig.Task):
    """Convert text case (default is "smart" conversion)."""
    upper: jiig.f.boolean('convert to all-uppercase', cli_flags='-u')
    lower: jiig.f.boolean('convert to all-lowercase', cli_flags='-l')
    blocks: jiig.f.text('text block(s) to convert', repeat=(1, None))

    def on_run(self, _runtime: jiig.Runtime):
        if self.upper and self.lower:
            raise RuntimeError('Conflicting upper/lower options specified.')
        if not self.upper and not self.lower:
            # "Smart" conversion checks first character of first block.
            to_upper = self.blocks[0][:1].islower()
        else:
            to_upper = self.upper
        text = ' '.join(self.blocks)
        if to_upper:
            output_text = text.upper()
        else:
            output_text = text.lower()
        print(output_text)
