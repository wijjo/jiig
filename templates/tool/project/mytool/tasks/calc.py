"""Sample Jiig task module."""

import jiig


class TaskCalc(jiig.Task):
    """Evaluate formula using Python interpreter."""
    blocks: jiig.text('formula block(s) to evaluate', repeat=(1, None))

    def on_run(self, _runtime: jiig.Runtime):
        result = eval(' '.join(self.blocks))
        print(f'The result is {result}.')
