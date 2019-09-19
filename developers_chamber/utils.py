import logging
import subprocess
import sys

from click import ClickException


LOGGER = logging.getLogger()


def call_command(command):
    try:
        LOGGER.info(command if isinstance(command, str) else ' '.join(command))
        subprocess.check_call(command, stdout=sys.stdout, shell=isinstance(command, str))
    except subprocess.CalledProcessError:
        raise ClickException('Command returned error')
