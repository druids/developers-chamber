import click
from click.formatting import HelpFormatter
from gettext import gettext as _
from developers_chamber.click.alias import AliasCommand


class FullHelpGroup(click.Group):
    def format_commands(self, ctx, formatter) -> None:
        """Extra format methods for multi methods that adds all the commands
        after the options.
        """
        all_commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command.  Ignore it
            if cmd is None:
                continue
            if cmd.hidden:
                continue

            all_commands.append((subcommand, cmd))

        alias_commands = [
            command for command in all_commands if isinstance(command[1], AliasCommand)
        ]
        commands = [
            command for command in all_commands if command not in alias_commands
        ]

        limit = formatter.width - 6 - max(len(cmd[0]) for cmd in all_commands)

        for commands, label in [
            (alias_commands, _("Aliases")),
            (commands, _("Commands")),
        ]:
            if len(commands):
                rows = []
                for subcommand, cmd in commands:
                    help = cmd.get_short_help_str(limit)
                    rows.append((subcommand, help))

                if rows:
                    with formatter.section(label):
                        formatter.write_dl(rows)


@click.group(cls=FullHelpGroup)
def cli():
    pass
