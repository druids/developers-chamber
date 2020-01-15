import click

from developers_chamber.scripts import cli
from developers_chamber.utils import call_command


@cli.command()
@click.argument('command')
def sh(command):
    """
    Runs SH command.
    """

    call_command(command)
