import logging
import os
import re
import subprocess
import sys

from click import ClickException
from git import Repo

LOGGER = logging.getLogger()
MIGRATIONS_PATTERN = r'\d+_migration\.py$'


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


class RepoMixin:
    """
    Mixin that provides functions for work with Git repository.
    """

    def _run_command(self, command):
        """
        Runs shell command and returns its output.
        """
        return subprocess.check_output(command, shell=True).decode().strip()

    def _get_repo(self):
        """
        Returns the repo object.
        """
        return Repo('.')

    def _get_active_branch_name(self):
        """
        Returns the repo active branch name
        """
        return self._get_repo().active_branch.name

    def _get_default_branch(self):
        """
        Returns default branch of the repo.
        """
        return self._run_command("git remote show origin | grep 'HEAD branch' | cut -d ':' -f 2 | tr -d ' '")

    def _get_diffs(self, target_branch=None):
        """
        Returns Git diffs against default branch.
        """
        repo = self._get_repo()
        target_branch = target_branch or getattr(repo.remotes.origin.refs, self._get_default_branch())
        target_commit = repo.merge_base(repo.active_branch, target_branch)[0]
        return target_commit.diff(repo.active_branch.name, create_patch=True)

    def _get_unstaged(self):
        """
        Returns unstaged files in the repo.
        """
        return self._get_repo().index.diff(None, create_patch=True)

    def _get_staged(self):
        """
        Returns staged files in the repo.
        """
        return self._get_repo().index.diff('HEAD')

    def _is_repo_clean(self):
        """
        Returns true, if repo is clean (no staged, unstaged or untracked files).
        """
        return not (self._get_staged() or self._get_unstaged() or self._get_repo().untracked_files)
