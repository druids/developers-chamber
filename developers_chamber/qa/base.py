import logging
import os
import re
import subprocess
import sys

import click
from click import ClickException

from developers_chamber.utils import MIGRATIONS_PATTERN, RepoMixin

LOGGER = logging.getLogger()


class QAError(Exception):
    """
    Generic QA exception that also carries command output.
    """

    def __init__(self, msg, output=None):
        super().__init__(msg)
        self.output = output.strip() if output is not None else None


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
            return super()._run_command(command)
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
        self._get_repo().git.reset('--hard', 'HEAD')

    def _is_python_file(self, path):
        return bool(re.search(r'\.py$', path))

    def _is_migration_file(self, path):
        return bool(re.search(MIGRATIONS_PATTERN, path))

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
                error_msg = click.style(str(ex), fg='red')
                if ex.output is not None:
                    error_msg = '\n'.join((error_msg, ex.output))
                self.results.append(error_msg)
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
