from developers_chamber.qa.base import QACheck, QACheckRunner
from developers_chamber.qa.checks import (ImportOrderQACheck,
                                          MigrationFilenamesQACheck,
                                          MissingMigrationsQACheck,
                                          MissingTranslationsQACheck,
                                          TestMethodNamesQACheck)
from developers_chamber.scripts import cli


@cli.group()
def qa():
    """Helpers for python project quality assurance."""


@qa.command()
def all():
    """
    Run all defined QA checks.
    """
    QACheckRunner(
        MissingMigrationsQACheck(),
        MigrationFilenamesQACheck(),
        MissingTranslationsQACheck(),
        TestMethodNamesQACheck(),
    ).run()


@qa.command()
def missing_migrations():
    """
    Run a missing Django migrations QA check. It will try to generate a Django migrations
    if there is one or more missing check is failed.
    """
    QACheckRunner(MissingMigrationsQACheck()).run()


@qa.command()
def migration_filenames():
    """
    Run migration filenames QA check.
    Migration name should be in format "[0-9]{4}_migration.py" (ex. 0001_migration.py)
    """
    QACheckRunner(MigrationFilenamesQACheck()).run()


@qa.command()
def missing_translations():
    """
    Run missing translations QA check. It will try to generate a Django makemessages
    if there is one or more missing check is failed.
    """
    QACheckRunner(MissingTranslationsQACheck()).run()


@qa.command()
def import_order():
    """
    Run import order QA check. It will check if all the new python code imports have the right order
    defined with isort command.
    """
    QACheckRunner(ImportOrderQACheck()).run()


@qa.command()
def test_method_names():
    """
    Runs test method names QA check. It will check if the new test methods has the right name in format defined in
    QA_DISALLOWED_TEST_METHOD_REGEXP setting.
    """
    QACheckRunner(TestMethodNamesQACheck()).run()
