"""
task mytask module

Refer to the documentation for more information about Task classes.
"""

import jiig


TASK = jiig.Task(
    description='mytask help description',
    args={
        'template_bool_option[!]': ('-b', 'a boolean option'),
        'template_string_option': ('-s', 'a string option'),
        'template_argument': 'an argument',
    },
)


@TASK.run
def task_run(_runner: jiig.Runner, data):
    if data.template_bool_option:
        print('template_bool_option is enabled.')
    if data.template_string_option:
        print(f'template_string_option="{data.template_string_option}"')
    print(f'template_argument="{data.template_argument}"')
