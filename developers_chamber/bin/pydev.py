#!/usr/bin/env python
import logging.config
import os
import sys
from pathlib import Path
from importlib.machinery import SourceFileLoader

import click_completion
import coloredlogs
from dotenv import load_dotenv
from developers_chamber.utils import INSTALLED_MODULES

for config_path in (Path.home(), Path.cwd()):
    if (config_path / ".pydev").exists() and (config_path / ".pydev").is_dir():
        for file in (config_path / ".pydev").iterdir():
            if (
                file.is_file()
                and file.suffix == ".conf"
                and not file.name.startswith("~")
            ):
                load_dotenv(dotenv_path=str(file), override=True)


from developers_chamber.scripts import cli

if "bitbucket" in INSTALLED_MODULES:
    from developers_chamber.scripts.bitbucket import *
from developers_chamber.scripts.docker import *

if "aws" in INSTALLED_MODULES:
    from developers_chamber.scripts.ecs import *

if "git" in INSTALLED_MODULES:
    from developers_chamber.scripts.git import *

from developers_chamber.scripts.gitlab import *

if "jira" in INSTALLED_MODULES:
    from developers_chamber.scripts.jira import *

if "qa" in INSTALLED_MODULES:
    from developers_chamber.scripts.qa import *

from developers_chamber.scripts.sh import *

if "slack" in INSTALLED_MODULES:
    from developers_chamber.scripts.slack import *

if "toggle" in INSTALLED_MODULES:
    from developers_chamber.scripts.toggle import *

from developers_chamber.scripts.version import *
from developers_chamber.scripts.project import *

click_completion.init()

# Import external scripts
for base_path in (Path.home(), Path.cwd()):
    if (base_path / ".pydev" / "scripts" / "__init__.py").exists():
        SourceFileLoader('*', str(base_path / ".pydev" / "scripts" / "__init__.py")).load_module()

from developers_chamber.scripts.init_aliasses import *

coloredlogs.install(milliseconds=True)


@cli.command()
@click.option(
    "--append/--overwrite", help="Append the completion code to the file", default=None
)
@click.option(
    "-i", "--case-insensitive/--no-case-insensitive", help="Case insensitive completion"
)
@click.argument(
    "shell",
    required=False,
    type=click_completion.DocumentedChoice(click_completion.core.shells),
)
@click.argument("path", required=False)
def init_completion(append, case_insensitive, shell, path):
    """Install the pydev completion"""
    extra_env = {"_PYDEV_CASE_INSENSITIVE_COMPLETE": "ON"} if case_insensitive else {}
    shell, path = click_completion.core.install(
        shell=shell, path=path, append=append, extra_env=extra_env
    )
    click.echo("{} completion installed in  {}".format(shell, path))


if __name__ == "__main__":
    cli()
