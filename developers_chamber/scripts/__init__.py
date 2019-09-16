import os
import json
import click


@click.group()
def cli():
    pass


for k, v in json.loads(os.environ.get('ALIASES', '{}')).items():
    def command_factory():
        alias_value = v

        def call_command_alias(ctx):
            cli.main(args=list(alias_value.split()) + ctx.args)
        call_command_alias.__doc__ = 'Alias to "{}"'.format(v)

        return call_command_alias

    cli.command(
        name=k,
        context_settings=dict(
            ignore_unknown_options=True,
            allow_extra_args=True
        )
    )(click.pass_context(command_factory()))
