"""
task template_task_name module

Refer to the documentation for more information about Task classes.
"""

import jiig


class TaskClass(jiig.Task):
    """template_task_name help description"""

    args = [
        jiig.BoolOpt('-b', 'template_bool_option', 'a boolean option'),
        jiig.Opt('-s', 'template_string_option', 'a string option'),
        jiig.Arg('template_argument', 'an argument'),
    ]

    def on_run(self):
        print('In on_run().')
        if self.data.template_bool_option:
            print('template_bool_option is enabled.')
        if self.data.template_string_option:
            print(f'template_string_option="{self.data.template_string_option}"')
        print(f'template_argument="{self.data.template_argument}"')
