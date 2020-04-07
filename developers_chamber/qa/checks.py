import os
import re

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
        last_line = output.split('\n')[-1]
        if last_line != 'No changes detected':
            raise QAError('Found missing migration(s)!', re.findall(r'\x1b.*?Migrations.+$', output, re.DOTALL)[0])


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
        self._run_command(self._get_command_from_config('QA_MAKE_MESSAGES_COMMAND'))

        translation_files = []
        for diff in self._get_unstaged():
            if self._is_translation_file(diff.b_path):
                translation_files.append(diff.b_path)

        if translation_files:
            raise QAError('Found changes in following translation file(s):', '\n'.join(translation_files))


class ImportOrderQACheck(QACheck):
    """
    Checks that isort applied on changed files does not introduce any changes.
    """
    name = 'Check import order'

    def _is_python_file(self, path):
        return bool(re.search(r'\.py$', path))

    def _run_check(self):
        changed_files = [diff.b_path for diff in self._get_diffs() if diff.b_path and self._is_python_file(diff.b_path)
                         and not self._is_migration_file(diff.b_path)]
        if changed_files:
            self._run_command('isort {}'.format(' '.join(changed_files)))
        else:
            return

        wrong_import_order_files = set(changed_files) & set([diff.b_path for diff in self._get_unstaged()])
        if wrong_import_order_files:
            raise QAError('Found unsorted import(s) in following file(s):', '\n'.join(wrong_import_order_files))
