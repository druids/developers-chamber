import logging
import os
import re
import subprocess
import sys

import click
from click import ClickException
from git import Repo

LOGGER = logging.getLogger()


class QAError(Exception):
    """
    Generic QA exception that also carries command output.
    """
    def __init__(self, msg, output):
        super().__init__(msg)
        self.output = output.strip()


class RepoMixin:
    """
    Mixin that provides functions for work with Git repository.
    """
    def _get_repo(self):
        """
        Returns the repo object.
        """
        return Repo('.')

    def _get_default_branch(self):
        """
        Returns default branch of the repo.
        """
        return self._run_command("git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'")

    def _get_diffs(self):
        """
        Returns Git diffs against default branch.
        """
        repo = self._get_repo()
        target_branch = getattr(repo.remotes.origin.refs, self._get_default_branch())
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


class QACheck(RepoMixin):
    """
    Base class for a quality assurance check.

    Arguments:
        name: Name of the check.
    """
    name = None

    def _get_command_from_config(self, command_config):
        """
        Returns command from config stored under `command_config` setting.
        """
        command = os.environ.get(command_config)
        if command is None:
            raise RuntimeError('Command config {} not defined!'.format(command_config))
        return '{} {}'.format(sys.argv[0], command)

    def _run_command(self, command):
        """
        Runs shell command and returns its output.
        """
        try:
            return subprocess.check_output(command, shell=True).decode().strip()
        except subprocess.CalledProcessError as ex:
            raise QAError(str(ex), ex.output.decode())

    def _run_check(self):
        """
        This function should implement the actual check and should raise `QAError` if failed.
        """
        raise NotImplementedError()

    def _cleanup(self):
        """
        Cleans up the repo to be fresh for another check.
        """
        self._get_repo().git.stash('save')

    def _is_migration_file(self, path):
        return bool(re.search(r'migrations\/([^\/]+)\.py$', path))

    def run(self):
        """
        Runs the check and cleanup methods.
        """
        try:
            self._run_check()
        finally:
            self._cleanup()


class QACheckRunner(RepoMixin):
    """
    Runs multiple checks and evaluates the results while printing a nice output.
    """
    LINE_LENGTH = 80

    def __init__(self, *checks):
        """
        Arguments:
            checks: Instances of QACheck class.
        """
        self.checks = checks
        self.results = []
        self.success = True

    def _print_line(self):
        LOGGER.info('-' * self.LINE_LENGTH)

    def _print_title(self, title):
        self._print_line()
        LOGGER.info(click.style(title, fg='blue', bold=True))
        self._print_line()

    def _run_checks(self):
        self._print_title('QA - running checks')
        for i, check in enumerate(self.checks):
            LOGGER.info(click.style('[{}/{}] {}...'.format(i + 1, len(self.checks), check.name), fg='blue'))
            try:
                check.run()
            except QAError as ex:
                self.results.append(click.style('{}\n{}'.format(click.style(str(ex), fg='red'), ex.output)))
                self.success = False
            else:
                self.results.append(click.style(' OK ', bg='green'))

    def _print_results(self):
        self._print_title('QA - results')
        for i, result in enumerate(self.results):
            LOGGER.info(click.style('#{} {}'.format(i + 1, self.checks[i].name), fg='blue'))
            LOGGER.info(result)

    def run(self):
        if not self._is_repo_clean():
            raise ClickException(
                'QA check requires repository to be clean, please remove any staged, unstaged or untracked files.'
            )

        self._run_checks()
        self._print_results()
        if not self.success:
            raise ClickException('QA check failed!')
