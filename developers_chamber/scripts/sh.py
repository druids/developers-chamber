import shlex

import click

from developers_chamber.scripts import cli
from developers_chamber.utils import call_command


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("command", nargs=-1, required=True)
def sh(command):
    """
    Run shell command and print the result.

    The command can be given as one quoted string or as the rest of the command line. A single
    argument is passed to the shell as it is, so it may contain the shell operators, while more
    arguments are joined back with their quoting kept.
    """
    call_command(command[0] if len(command) == 1 else shlex.join(command))
