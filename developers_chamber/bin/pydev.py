#!/usr/bin/env python
import logging.config
import sys
import os
from pathlib import Path

import click_completion
import coloredlogs
from dotenv import load_dotenv


for config_path in (Path.home(), Path.cwd()):
    if (config_path / '.pydev').exists() and (config_path / '.pydev').is_dir():
        for file in (config_path / '.pydev').iterdir():
            if file.is_file() and file.suffix == '.conf' and not file.name.startswith('~'):
                load_dotenv(dotenv_path=str(file), override=True)


from developers_chamber.scripts import cli
from developers_chamber.scripts.bitbucket import *
from developers_chamber.scripts.docker import *
from developers_chamber.scripts.ecs import *
from developers_chamber.scripts.git import *
from developers_chamber.scripts.gitlab import *
from developers_chamber.scripts.jira import *
from developers_chamber.scripts.project import *
from developers_chamber.scripts.qa import *
from developers_chamber.scripts.sh import *
from developers_chamber.scripts.slack import *
from developers_chamber.scripts.toggle import *
from developers_chamber.scripts.version import *
from developers_chamber.scripts.init_aliasses import *


click_completion.init()


# Import external scripts
for base_path in (Path.home(), Path.cwd()):
    if (base_path / '.pydev' / 'scripts').exists():
        sys.path.append(base_path / '.pydev')
        import scripts


coloredlogs.install(milliseconds=True)


@cli.command()
@click.option('--append/--overwrite', help="Append the completion code to the file", default=None)
@click.option('-i', '--case-insensitive/--no-case-insensitive', help="Case insensitive completion")
@click.argument('shell', required=False, type=click_completion.DocumentedChoice(click_completion.core.shells))
@click.argument('path', required=False)
def init_completion(append, case_insensitive, shell, path):
    """Install the pydev completion"""
    extra_env = {'_PYDEV_CASE_INSENSITIVE_COMPLETE': 'ON'} if case_insensitive else {}
    shell, path = click_completion.core.install(shell=shell, path=path, append=append, extra_env=extra_env)
    click.echo('{} completion installed in  {}'.format(shell, path))


if __name__ == "__main__":
    cli()
