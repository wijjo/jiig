"""
task mytask module

Refer to the documentation for more information about Task classes.
"""

import jiig


@jiig.task(
    cli={
        'options': {
            'template_bool_option': '-b',
            'template_string_option': ('-s', '--string'),
        }
    }
)
def mytask(
    runtime: jiig.Runtime,
    template_bool_option: jiig.f.boolean(),
    template_string_option: jiig.f.text(),
    template_argument_positional: jiig.f.text(),
):
    """
    mytask help description

    :param runtime: jiig runtime api
    :param template_bool_option: a boolean option
    :param template_string_option: a string option
    :param template_argument_positional: a positional argument
    """
    if template_bool_option:
        runtime.message('template_bool_option is enabled.')
    if template_string_option:
        runtime.message(f'template_string_option="{template_string_option}"')
    runtime.message(f'template_argument_positional="{template_argument_positional}"')
