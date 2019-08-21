#!/usr/bin/env python
from dotenv import load_dotenv

load_dotenv(dotenv_path='./config/pydev.conf')

from developers_chamber.scripts import cli
from developers_chamber.scripts.bitbucket import *
from developers_chamber.scripts.ecs import *
from developers_chamber.scripts.git import *
from developers_chamber.scripts.version import *


if __name__ == '__main__':
    cli()
