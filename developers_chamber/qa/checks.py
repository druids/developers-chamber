import os
import re
import time

from developers_chamber.utils import remove_ansi

from .base import QACheck, QAError


class MissingMigrationsQACheck(QACheck):
    """
    Checks that make migrations command does not generate new migrations.
    """
    name = 'Check missing migrations'

    def _run_check(self):
        output = self._run_command(
            '{}{}'.format(self._get_command_from_config('QA_MAKE_MIGRATIONS_COMMAND'), ' --dry-run')
        )
        if not re.search('No changes detected', output):
            raise QAError(
                'Found missing migration(s)!',
                re.findall(r'Migrations.+$', remove_ansi(output), re.DOTALL)[0]
            )


class MigrationFilenamesQACheck(QACheck):
    """
    Checks that new migrations introduced in the branch have correct names.
    """
    name = 'Check migration filenames'

    def _is_migration_file_with_wrong_name(self, path):
        return self._is_migration_file(path) and not re.search(r'/([0-9]{4}_migration|__init__)\.py$', str(path))

    def _run_check(self):
        wrong_name_files = []
        for diff in self._get_diffs():
            if diff.new_file and self._is_migration_file_with_wrong_name(diff.b_path):
                wrong_name_files.append(diff.b_path)

        if wrong_name_files:
            raise QAError('Found wrongly named migration file(s):', '\n'.join(wrong_name_files))


class MissingTranslationsQACheck(QACheck):
    """
    Checks that generating translations does not introduce any changes.
    """
    name = 'Check missing translations'

    def _is_translation_file(self, path):
        return bool(re.search(r'django\.po$', str(path)))

    def _run_check(self):
        start_time = time.time()
        self._run_command(self._get_command_from_config('QA_MAKE_MESSAGES_COMMAND'))

        changed_translation_files = []
        for diff in self._get_unstaged():
            if self._is_translation_file(diff.b_path):
                changed_translation_files.append(diff.b_path)

        if changed_translation_files:
            raise QAError('Found changes in following translation file(s):', '\n'.join(changed_translation_files))

        # At this point, no changes were detected, which makes this check to pass.
        # However we need to check, that at least modification time of any translation file changed,
        # otherwise the result could be false positive.

        for translation_file in self._run_command('find ./ -type f -name "*.po"').split('\n'):
            if os.path.getmtime(translation_file) > start_time:
                return

        raise QAError(
            'No translation were touched, either QA_MAKE_MESSAGES_COMMAND is not working or changed files are not '
            'visible (for example the command is run inside a Docker container without volume being exposed outside).'
        )


class ImportOrderQACheck(QACheck):
    """
    Checks that isort applied on changed files does not introduce any changes.
    """
    name = 'Check import order'

    def _run_check(self):
        changed_files = [diff.b_path for diff in self._get_diffs() if diff.b_path and self._is_python_file(diff.b_path)
                         and not self._is_migration_file(diff.b_path)]
        if changed_files:
            self._run_command('isort {}'.format(' '.join(changed_files)))
        else:
            return

        wrong_import_order_files = set(changed_files) & set([diff.b_path for diff in self._get_unstaged()])
        if wrong_import_order_files:
            raise QAError(
                'Found unsorted import(s) in following file(s):',
                (
                    '\n'.join(wrong_import_order_files) +
                    '\n\n' +
                    'To fix it run: "isort {}"'.format(' '.join(wrong_import_order_files))
                )
            )


class RegexPyQACheck(QACheck):
    """
    Helper for writing QAChecks which finds invalid regex patterns in python code.
    """

    pattern = None

    def _run_check(self):
        if self.pattern:
            invalid_patterns = []
            for diff_obj in self._get_diffs():
                if diff_obj.b_path and self._is_python_file(diff_obj.b_path):
                    for line in diff_obj.diff.decode().split('\n'):
                        if line.startswith('+'):
                            match = re.search(self.pattern, line[1:])
                            if match:
                                invalid_patterns.append((diff_obj.b_path, match[1]))

            if invalid_patterns:
                self._found_invalid_patterns(invalid_patterns)

    def _found_invalid_patterns(self, invalid_patterns):
        raise NotImplementedError


class TestMethodNamesQACheck(RegexPyQACheck):
    """
    Checks that test methods are named correctly.

    `QA_DISALLOWED_TEST_METHOD_NAME_REGEXP` should define regexp to match disallowed test method name(s) in the diff.
    The regexp should include one capturing group (preferably matching the entire test method name), that will be
    printed out to identify the problematic test method.
    """
    name = 'Check test method names'

    pattern = os.environ.get('QA_DISALLOWED_TEST_METHOD_REGEXP')

    def _found_invalid_patterns(self, invalid_patterns):
        raise QAError(
            'Found disallowed test method name(s):',
            '\n'.join(('{}: {}'.format(file, value) for file, value in invalid_patterns))
        )

