"""
task mytask module

Refer to the documentation for more information about Task functions.
"""

from jiig import fields
from jiig.task import task
from jiig.runtime import Runtime


@task(
    cli={
        'options': {
            'template_bool_option': '-b',
            'template_string_option': ('-s', '--string'),
        }
    }
)
def mytask(
    runtime: Runtime,
    template_bool_option: fields.boolean(),
    template_string_option: fields.text(),
    template_argument_positional: fields.text(),
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
