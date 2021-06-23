"""Sample Jiig task module."""

import jiig


class TaskWords(jiig.Task):
    """Count words using primitive whitespace splitting."""
    blocks: jiig.f.text('text block(s) with words to count', repeat=(1, None))

    def on_run(self, _runtime: jiig.Runtime):
        count = len(' '.join(self.blocks).split())
        print(f'The word count is {count}.')
