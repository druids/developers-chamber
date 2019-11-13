#!/usr/bin/env python
import sys

import logging.config

from pathlib import Path

from dotenv import load_dotenv

import coloredlogs

# Load configuration
for config_path in (Path.home(), Path.cwd()):
    if (config_path / '.pydev').exists() and (config_path / '.pydev').is_dir():
        for file in (config_path / '.pydev').iterdir():
            if file.is_file() and file.suffix == '.conf':
                load_dotenv(dotenv_path=str(file))

from developers_chamber.scripts import cli
from developers_chamber.scripts.bitbucket import *
from developers_chamber.scripts.docker import *
from developers_chamber.scripts.ecs import *
from developers_chamber.scripts.git import *
from developers_chamber.scripts.project import *
from developers_chamber.scripts.qa import *
from developers_chamber.scripts.version import *
from developers_chamber.scripts.sh import *


# Import external scripts
for base_path in (Path.home(), Path.cwd()):
    if (base_path / '.pydev' / 'scripts').exists():
        sys.path.append(base_path / '.pydev')
        import scripts


coloredlogs.install(milliseconds=True)

if __name__ == '__main__':
    cli()
