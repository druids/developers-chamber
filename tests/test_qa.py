import sys

import pytest
from click import ClickException

from developers_chamber.qa.base import QACheck, QACheckRunner, QAError
from developers_chamber.qa.checks import (
    MigrationFilenamesQACheck,
    MissingTranslationsQACheck,
)


class RecordingQACheck(QACheck):
    """Check which records that the cleanup ran instead of resetting the repository."""

    name = "Recording check"

    def __init__(self, error=None):
        self.error = error
        self.cleaned_up = False

    def _run_check(self):
        if self.error:
            raise self.error

    def _cleanup(self):
        self.cleaned_up = True


@pytest.fixture
def run_checks(monkeypatch):
    """Runs a check runner over a clean repository."""

    def run(*checks):
        monkeypatch.setattr(QACheckRunner, "_is_repo_clean", lambda self: True)
        runner = QACheckRunner(*checks)
        runner.run()
        return runner

    return run


class TestQAError:

    def test_output_is_stripped(self):
        assert QAError("failed", "  boom  \n").output == "boom"

    def test_output_is_optional(self):
        assert QAError("failed").output is None

    def test_message_is_kept(self):
        assert str(QAError("failed", "boom")) == "failed"


class TestQACheck:

    @pytest.mark.parametrize(
        ("path", "expected"),
        [("a/b/c.py", True), ("a/b/c.pyc", False), ("a/b/c.txt", False)],
    )
    def test_python_file_is_recognized(self, path, expected):
        assert QACheck()._is_python_file(path) is expected

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("app/migrations/0001_initial.py", True),
            ("app/models.py", False),
            ("app/migrations/sub/0001_initial.py", False),
        ],
    )
    def test_migration_file_is_recognized(self, path, expected):
        assert QACheck()._is_migration_file(path) is expected

    def test_command_is_built_from_the_config(self, monkeypatch):
        monkeypatch.setenv("QA_TEST_COMMAND", "run tests")
        assert QACheck()._get_command_from_config(
            "QA_TEST_COMMAND"
        ) == "{} run tests".format(sys.argv[0])

    def test_missing_command_config_is_reported(self, monkeypatch):
        monkeypatch.delenv("QA_TEST_COMMAND", raising=False)
        with pytest.raises(RuntimeError, match="QA_TEST_COMMAND not defined"):
            QACheck()._get_command_from_config("QA_TEST_COMMAND")

    def test_command_output_is_returned(self):
        assert QACheck()._run_command("echo hi") == "hi"

    def test_failed_command_is_turned_into_a_qa_error_with_its_output(self):
        with pytest.raises(QAError) as error:
            QACheck()._run_command("echo boom; exit 1")
        assert error.value.output == "boom"

    def test_base_check_has_no_implementation(self):
        with pytest.raises(NotImplementedError):
            QACheck()._run_check()

    def test_cleanup_runs_after_a_successful_check(self):
        check = RecordingQACheck()
        check.run()
        assert check.cleaned_up

    def test_cleanup_runs_after_a_failed_check(self):
        check = RecordingQACheck(error=QAError("failed"))
        with pytest.raises(QAError):
            check.run()
        assert check.cleaned_up


class TestChecks:

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("app/migrations/0001_migration.py", False),
            ("app/migrations/__init__.py", False),
            ("app/migrations/0001_initial.py", True),
            ("app/models.py", False),
        ],
        ids=["correct name", "init", "wrong name", "outside migrations"],
    )
    def test_migration_filename_is_checked(self, path, expected):
        check = MigrationFilenamesQACheck()
        assert check._is_migration_file_with_wrong_name(path) is expected

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("locale/cs/LC_MESSAGES/django.po", True),
            ("locale/cs/LC_MESSAGES/django.mo", False),
            ("app/models.py", False),
        ],
    )
    def test_translation_file_is_recognized(self, path, expected):
        assert MissingTranslationsQACheck()._is_translation_file(path) is expected


class TestQACheckRunner:

    def test_all_checks_run_and_succeed(self, run_checks):
        checks = (RecordingQACheck(), RecordingQACheck())
        runner = run_checks(*checks)
        assert runner.success
        assert len(runner.results) == 2
        assert all(check.cleaned_up for check in checks)

    def test_failed_check_fails_the_whole_run(self, run_checks):
        checks = (RecordingQACheck(error=QAError("failed", "boom")), RecordingQACheck())
        with pytest.raises(ClickException, match="QA check failed!"):
            run_checks(*checks)
        assert checks[1].cleaned_up, "the remaining checks still run"

    def test_dirty_repository_stops_the_run(self, monkeypatch):
        check = RecordingQACheck()
        monkeypatch.setattr(QACheckRunner, "_is_repo_clean", lambda self: False)
        with pytest.raises(ClickException, match="requires repository to be clean"):
            QACheckRunner(check).run()
        assert not check.cleaned_up
