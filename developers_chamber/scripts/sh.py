import click

from developers_chamber.scripts import cli
from developers_chamber.utils import call_command


@cli.command(
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True)
)
@click.argument("command")
def sh(command):
    """
    Run shell command and print the result.
    """
    call_command(command)
