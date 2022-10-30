import json
import os
import re
import shlex

import click
from click.formatting import wrap_text

from gettext import gettext as _

from developers_chamber.scripts import cli


def find_and_replace_command_variable(arg, command):
    match = re.match(r'^--(?P<arg_name>[^=\ ]+)[\ =](?P<arg_value>.+)', arg)
    if match:
        arg_name, arg_value = match.groups()
        if '${}'.format(arg_name) in command:
            return True, command.replace('${}'.format(arg_name), arg_value)
        elif '${}'.format(arg_name.replace('-', '_')) in command:
            return True, command.replace('${}'.format(arg_name.replace('-', '_')), arg_value)
    return False, command


def parse_alias(alias):
    command_parts = list(shlex.split(alias))
    used_command_parts = []

    click_command = cli
    while command_parts:
        command_part = command_parts[0]
        current_click_command = click_command.get_command(None, command_part)
        if current_click_command is None:
            raise click.ClickException('Command to the alias "{}" cannot be found'.format(alias))

        used_command_parts.append(command_parts.pop(0))
        click_command = current_click_command
        if not isinstance(current_click_command, click.Group):
            break
    return used_command_parts, command_parts, click_command, alias


class AliasCommand(click.Command):

    def __init__(self, commands, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parse_alias(commands)

    def _parse_alias(self, commands):
        commands = [commands] if isinstance(commands, str) else commands
        self.aliases = [
            (parse_alias(alias)) for alias in commands
        ]

    def format_help_text(self, ctx, formatter) -> None:
        formatter.write_paragraph()
        with formatter.indentation():
            formatter.write_text('Alias to commands: ')
            with formatter.indentation():
                for used_command_parts, remaining_command_parts, click_command, alias_str in self.aliases:
                    formatter.write_text('* ' + ' '.join(used_command_parts))
                    if remaining_command_parts:
                        with formatter.indentation(), formatter.indentation():
                            formatter.write_text(' '.join(remaining_command_parts))

    def format_epilog(self, ctx, formatter) -> None:
        with formatter.section(_('Commands in alias help')):
            for used_command_parts, remaining_command_parts, click_command, alias_str in self.aliases:
                with formatter.indentation():
                    formatter.write_paragraph()
                    formatter.write_text('* ' + ' '.join(used_command_parts))
                    with formatter.indentation(), formatter.indentation():
                        click_command.format_help_text(ctx, formatter)
                        click_command.format_options(ctx, formatter)
                        formatter.write_paragraph()

    def invoke(self, ctx):
        for i, (used_command_parts, remaining_command_parts, click_command, alias_str) in enumerate(self.aliases):
            if i == 0:
                alias_args = []
                for arg in ctx.args:
                    replaced_arg, alias_str = find_and_replace_command_variable(arg, alias_str)
                    if not replaced_arg:
                        alias_args.append(arg)

            cli.main(args=shlex.split(alias_str) + alias_args, standalone_mode=False)


for k, v in json.loads(os.environ.get('ALIASES', '{}')).items():
    cli.add_command(
        AliasCommand(
            commands=v,
            name=k,
            context_settings=dict(
                ignore_unknown_options=True,
                allow_extra_args=True
            ),
        )
    )
