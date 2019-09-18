import re
import os
import json
import click
import shlex


@click.group()
def cli():
    pass


def find_and_replace_command_variable(arg, command):
    match = re.match(r'^--(?P<arg_name>[^=\ ]+)[\ =](?P<arg_value>.+)', arg)
    if match:
        arg_name, arg_value = match.groups()
        if '${}'.format(arg_name) in command:
            return True, command.replace('${}'.format(arg_name), arg_value)
        elif '${}'.format(arg_name.replace('-', '_')) in command:
            return True, command.replace('${}'.format(arg_name.replace('-', '_')), arg_value)
    return False, command


for k, v in json.loads(os.environ.get('ALIASES', '{}')).items():
    def command_factory():
        alias_value = v

        def call_command_alias(ctx):
            command = alias_value

            # Replace variable arguments
            alias_args = []
            for arg in ctx.args:
                replaced_arg, command = find_and_replace_command_variable(arg, command)
                if not replaced_arg:
                    alias_args.append(arg)

            cli.main(args=shlex.split(command) + alias_args)
        call_command_alias.__doc__ = 'Alias to "{}"'.format(v)

        return call_command_alias

    cli.command(
        name=k,
        context_settings=dict(
            ignore_unknown_options=True,
            allow_extra_args=True
        )
    )(click.pass_context(command_factory()))
