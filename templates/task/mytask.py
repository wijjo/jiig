"""
task mytask module

Refer to the documentation for more information about Task classes.
"""

import jiig


class Task(jiig.Task):
    """mytask help description"""

    template_bool_option: jiig.f.boolean('a boolean option', cli_flags='-b')
    template_string_option: jiig.f.text('a string option', cli_flags='-s')
    template_argument_positional: jiig.f.text('a positional argument')

    def on_run(self, _runtime: jiig.Runtime):
        if self.template_bool_option:
            print('template_bool_option is enabled.')
        if self.template_string_option:
            print(f'template_string_option="{self.template_string_option}"')
        print(f'template_argument_positional="{self.template_argument_positional}"')
