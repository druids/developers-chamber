import click

from developers_chamber.scripts import cli

from developers_chamber.utils import call_command


@cli.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True
    )
)
@click.argument('command')
@click.pass_context
def sh(ctx, command):
    """
    Runs SH command.
    """

    call_command(' '.join([command] + ctx.args))
