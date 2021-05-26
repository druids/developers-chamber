import os
import logging
import re
import subprocess
import sys

from click import ClickException

LOGGER = logging.getLogger()


def call_command(command, quiet=False, env=None):
    env = {} if env is None else env
    try:
        if not quiet:
            LOGGER.info(command if isinstance(command, str) else ' '.join(command))
        subprocess.check_call(command, stdout=sys.stdout, shell=isinstance(command, str), env=dict(os.environ, **env))
    except subprocess.CalledProcessError:
        raise ClickException('Command returned error')


def call_compose_command(command, quiet=False, env=None):
    env = {} if env is None else env
    if not quiet:
        LOGGER.info(command if isinstance(command, str) else ' '.join(command))
    compose_process = subprocess.Popen(
        command, stdout=sys.stdout, shell=isinstance(command, str), env=dict(os.environ, **env)
    )
    try:
        if compose_process.wait() != 0:
            raise ClickException('Command returned error')
    except KeyboardInterrupt:
        try:
            compose_process.wait()
        except KeyboardInterrupt:
            compose_process.wait()


def pretty_time_delta(seconds):
    seconds = abs(int(seconds))
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if hours > 0:
        return '{}h {}m {}s'.format(hours, minutes, seconds)
    elif minutes > 0:
        return '{}m {}s'.format(minutes, seconds)
    else:
        return '{}s'.format(seconds)


def remove_ansi(input):
    """
    Remove non-visible characters (like color sequences etc.).
    """
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', input)
