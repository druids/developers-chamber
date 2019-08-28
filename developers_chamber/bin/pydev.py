#!/usr/bin/env python
import logging.config

from developers_chamber.scripts import cli
from developers_chamber.scripts.bitbucket import *
from developers_chamber.scripts.docker import *
from developers_chamber.scripts.ecs import *
from developers_chamber.scripts.git import *
from developers_chamber.scripts.version import *
from dotenv import load_dotenv

load_dotenv(dotenv_path='./config/pydev.conf')

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
