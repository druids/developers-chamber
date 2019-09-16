#!/usr/bin/env python
import sys

import logging.config

from pathlib import Path

from dotenv import load_dotenv

# Load configuration
load_dotenv(dotenv_path=str(Path.home() / '.pydev' / 'pydev.conf'))
load_dotenv(dotenv_path=str(Path.cwd() / '.pydev' / 'pydev.conf'))

from developers_chamber.scripts import cli
from developers_chamber.scripts.bitbucket import *
from developers_chamber.scripts.docker import *
from developers_chamber.scripts.ecs import *
from developers_chamber.scripts.git import *
from developers_chamber.scripts.project import *
from developers_chamber.scripts.version import *


# Import external scripts
for base_path in (Path.home(), Path.cwd()):
    if (base_path / '.pydev' / 'scripts').exists():
        sys.path.append(base_path / '.pydev')
        import scripts


LOGGING = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s]: %(message)s',
        },
    },
    'handlers': {
        'default': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ('default',),
            'level': 'INFO',
        },
    },
}
logging.config.dictConfig(LOGGING)


if __name__ == '__main__':
    cli()
