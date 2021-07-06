"""
task mytask module

Refer to the documentation for more information about Task classes.
"""

import jiig


@jiig.task
def mytask(
    runtime: jiig.Runtime,
    template_bool_option: jiig.f.boolean('a boolean option', cli_flags='-b'),
    template_string_option: jiig.f.text('a string option', cli_flags='-s'),
    template_argument_positional: jiig.f.text('a positional argument'),
):
    """mytask help description"""
    if template_bool_option:
        runtime.message('template_bool_option is enabled.')
    if template_string_option:
        runtime.message(f'template_string_option="{template_string_option}"')
    runtime.message(f'template_argument_positional="{template_argument_positional}"')
