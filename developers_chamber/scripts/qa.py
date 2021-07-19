from developers_chamber.qa.base import QACheck, QACheckRunner
from developers_chamber.qa.checks import (ImportOrderQACheck,
                                          MigrationFilenamesQACheck,
                                          MissingMigrationsQACheck,
                                          MissingTranslationsQACheck,
                                          TestMethodNamesQACheck,
                                          TestPrintStatementsQACheck)
from developers_chamber.scripts import cli


@cli.group()
def qa():
    """
    Quality assurance commands.
    """

@qa.command()
def all():
    """
    Runs all defined QA checks.
    """
    QACheckRunner(
        MissingMigrationsQACheck(),
        MigrationFilenamesQACheck(),
        MissingTranslationsQACheck(),
        ImportOrderQACheck(),
        TestMethodNamesQACheck(),
        TestPrintStatementsQACheck(),
    ).run()


@qa.command()
def missing_migrations():
    """
    Runs missing migrations QA check.
    """
    QACheckRunner(MissingMigrationsQACheck()).run()


@qa.command()
def migration_filenames():
    """
    Runs migration filenames QA check.
    """
    QACheckRunner(MigrationFilenamesQACheck()).run()


@qa.command()
def missing_translations():
    """
    Runs missing translations QA check.
    """
    QACheckRunner(MissingTranslationsQACheck()).run()


@qa.command()
def import_order():
    """
    Runs import order QA check.
    """
    QACheckRunner(ImportOrderQACheck()).run()


@qa.command()
def test_method_names():
    """
    Runs test method names QA check.
    """
    QACheckRunner(TestMethodNamesQACheck()).run()


@qa.command()
def test_print_statements():
    """
    Runs test method names QA check.
    """
    QACheckRunner(TestPrintStatementsQACheck()).run()
