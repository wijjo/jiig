"""Sample Jiig "hello world" task module."""

import jiig


class TaskClass(jiig.Task):
    """Display hello message."""

    args = {
        'TEXAS_STYLE!': ('-t', 'greet with a drawl'),
        'NAME?': 'optional name',
    }

    def on_run(self):
        greeting = 'Howdy' if self.data.TEXAS_STYLE else 'Hello'
        if self.data.NAME:
            greeting = f'{greeting} {self.data.NAME}'
        jiig.utility.process.run(['date'], quiet=True)
        print(f'{greeting}:')
        print('')
        print(f'Sample task script: "template_tool_name"')
        print('')
        print('Use the sample script as a basis for defining your own custom')
        print('tool, tasks, options, and arguments.')
