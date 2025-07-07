import re
import shlex
from gettext import gettext as _

import click
from click.formatting import wrap_text


def find_and_replace_command_variable(arg, command, index):
    match = re.match(r"^--(?P<arg_name>[^=\ ]+)[\ =](?P<arg_value>.+)", arg)
    if match:
        arg_name, arg_value = match.groups()
        if f"${arg_name}" in command:
            return True, command.replace(f"${arg_name}", arg_value)
        elif f'${arg_name.replace("-", "_")}' in command:
            return True, command.replace(f'${arg_name.replace("-", "_")}', arg_value)
    if f"${index}" in command:
        return True, command.replace(f"${index}", arg)
    return False, command


def parse_alias(alias):
    from developers_chamber.scripts import cli

    command_parts = list(shlex.split(alias))
    used_command_parts = []

    click_command = cli
    while command_parts:
        command_part = command_parts[0]
        current_click_command = click_command.get_command(None, command_part)
        if current_click_command is None:
            raise click.ClickException(
                'Command to the alias "{}" cannot be found'.format(alias)
            )

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
        if isinstance(commands, str):
            commands = [commands]
            description = ""
        elif isinstance(commands, list):
            commands = commands
            description = ""
        elif isinstance(commands, dict):
            description = commands["description"]
            commands = commands["command"]
        else:
            raise click.ClickException("Invalid alias type")

        commands = [commands] if isinstance(commands, str) else commands
        self.aliases = [(parse_alias(alias)) for alias in commands]
        self.short_help = description

    def format_help_text(self, ctx, formatter) -> None:
        formatter.write_paragraph()
        with formatter.indentation():
            if self.short_help:
                formatter.write_text(self.short_help)
                formatter.write_paragraph()
            formatter.write_text("Alias to commands: ")
            with formatter.indentation():
                for (
                    used_command_parts,
                    remaining_command_parts,
                    click_command,
                    alias_str,
                ) in self.aliases:
                    formatter.write_text("* " + " ".join(used_command_parts))
                    if remaining_command_parts:
                        with formatter.indentation(), formatter.indentation():
                            formatter.write_text(" ".join(remaining_command_parts))

    def format_epilog(self, ctx, formatter) -> None:
        with formatter.section(_("Commands in alias help")):
            for (
                used_command_parts,
                remaining_command_parts,
                click_command,
                alias_str,
            ) in self.aliases:
                with formatter.indentation():
                    formatter.write_paragraph()
                    formatter.write_text("* " + " ".join(used_command_parts))
                    with formatter.indentation(), formatter.indentation():
                        click_command.format_help_text(ctx, formatter)
                        click_command.format_options(ctx, formatter)
                        formatter.write_paragraph()

    def shell_complete(self, ctx, param):
        from click.shell_completion import CompletionItem

        return [CompletionItem(param, type="file")]

    def invoke(self, ctx):
        from developers_chamber.scripts import cli

        for i, (
            used_command_parts,
            remaining_command_parts,
            click_command,
            alias_str,
        ) in enumerate(self.aliases):
            if i == 0:
                alias_args = []

                for index, arg in enumerate(ctx.args, start=1):
                    replaced_arg, alias_str = find_and_replace_command_variable(
                        arg, alias_str, index
                    )
                    if not replaced_arg:
                        alias_args.append(arg)

                if "$@" in alias_str:
                    alias_str = alias_str.replace("$@", " ".join(ctx.args))
                    alias_args = []

            cli.main(args=shlex.split(alias_str) + alias_args, standalone_mode=False)
