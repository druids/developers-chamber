import click
import pytest
from click.testing import CliRunner

from developers_chamber.click.options import (
    COMMA_SEPARATED,
    CommaSeparatedPathType,
    ContainerCommandType,
    ContainerDirToCopyType,
    ContainerEnvironment,
)


def resolve_from_envvar(type_, env_value):
    """Value which a repeatable option builds out of one environment variable."""

    @click.command()
    @click.option("-o", "values", type=type_, multiple=True, envvar="PYDEV_TEST")
    def cmd(values):
        click.echo(repr(values))

    result = CliRunner().invoke(cmd, [], env={"PYDEV_TEST": env_value})
    if result.exit_code:
        raise AssertionError(result.output.strip())
    return result.output.strip()


class TestEnvvarSplitter:
    """The comma separating the items of a setting is declared by the type, not by the option."""

    def test_comma_separated_strings_are_split(self):
        assert (
            resolve_from_envvar(COMMA_SEPARATED, "base,static") == "('base', 'static')"
        )

    def test_single_item_stays_a_single_item(self):
        assert resolve_from_envvar(COMMA_SEPARATED, "base") == "('base',)"

    def test_comma_separated_paths_are_split(self):
        assert (
            resolve_from_envvar(CommaSeparatedPathType(), "a.yaml,b.yaml")
            == "('a.yaml', 'b.yaml')"
        )

    def test_structured_items_are_split_and_converted(self):
        assert (
            resolve_from_envvar(ContainerCommandType(), "base:migrate,static:build")
            == "(('base', 'migrate'), ('static', 'build'))"
        )

    def test_command_line_value_wins_over_the_environment(self):
        @click.command()
        @click.option(
            "-o", "values", type=COMMA_SEPARATED, multiple=True, envvar="PYDEV_TEST"
        )
        def cmd(values):
            click.echo(repr(values))

        result = CliRunner().invoke(
            cmd, ["-o", "other"], env={"PYDEV_TEST": "base,static"}
        )
        assert result.output.strip() == "('other',)"

    def test_trailing_separator_is_reported_instead_of_being_ignored(self):
        with pytest.raises(
            AssertionError, match='format must be "DOCKER_CONTAINER_NAME:COMMAND"'
        ):
            resolve_from_envvar(ContainerCommandType(), "base:migrate,")


class TestContainerDirToCopyType:

    def test_value_is_parsed_into_the_declared_fields(self):
        assert ContainerDirToCopyType().convert(
            "base:/usr/local/lib:var/lib", None, None
        ) == (
            "base",
            "/usr/local/lib",
            "var/lib",
        )

    def test_value_with_a_wrong_number_of_fields_fails_with_the_declared_format(self):
        with pytest.raises(
            click.UsageError,
            match='format must be "DOCKER_CONTAINER_NAME:CONTAINER_DIRECTORY:HOST_DIRECTORY"',
        ):
            ContainerDirToCopyType().convert("base:/usr/local/lib", None, None)

    def test_encoded_object_is_parsed_back(self):
        items = ContainerDirToCopyType.encode({"base": {"/usr/local/lib": "var/lib"}})
        assert items == ["base:/usr/local/lib:var/lib"]
        assert [
            ContainerDirToCopyType().convert(item, None, None) for item in items
        ] == [("base", "/usr/local/lib", "var/lib")]

    def test_every_container_directory_is_a_separate_item(self):
        assert ContainerDirToCopyType.encode(
            {"base": {"/a": "var/a", "/b": "var/b"}, "static": {"/c": "var/c"}}
        ) == ["base:/a:var/a", "base:/b:var/b", "static:/c:var/c"]

    @pytest.mark.parametrize("value", ["base:/a:var/a", ["base:/a:var/a"]])
    def test_string_and_list_are_kept_as_is(self, value):
        assert ContainerDirToCopyType.encode(value) == value

    def test_invalid_object_is_rejected(self):
        with pytest.raises(ValueError, match='container "base" must be an object'):
            ContainerDirToCopyType.encode({"base": "var/a"})


class TestContainerCommandType:

    def test_value_is_parsed_into_the_declared_fields(self):
        assert ContainerCommandType().convert(
            "base:./manage.py migrate", None, None
        ) == (
            "base",
            "./manage.py migrate",
        )

    def test_empty_value_is_rejected(self):
        # an empty item comes from a trailing separator in the setting, returning nothing here
        # used to put a None into the option value which the caller could not unpack
        with pytest.raises(
            click.UsageError, match='format must be "DOCKER_CONTAINER_NAME:COMMAND"'
        ):
            ContainerCommandType().convert("", None, None)

    def test_value_with_a_wrong_number_of_fields_fails_with_the_declared_format(self):
        with pytest.raises(
            click.UsageError, match='format must be "DOCKER_CONTAINER_NAME:COMMAND"'
        ):
            ContainerCommandType().convert("base", None, None)

    def test_encoded_object_is_parsed_back(self):
        items = ContainerCommandType.encode({"base": "./manage.py migrate"})
        assert items == ["base:./manage.py migrate"]
        assert [ContainerCommandType().convert(item, None, None) for item in items] == [
            ("base", "./manage.py migrate")
        ]

    def test_command_must_be_a_string(self):
        with pytest.raises(ValueError, match='"base" must be a string'):
            ContainerCommandType.encode({"base": ["./manage.py migrate"]})


class TestContainerEnvironment:

    def test_value_is_parsed_into_variables(self):
        assert ContainerEnvironment().convert("DEBUG=1 ENV=local", None, None) == {
            "DEBUG": "1",
            "ENV": "local",
        }

    def test_value_containing_the_assignment_is_kept_whole(self):
        assert ContainerEnvironment().convert(
            "DSN=db://user:pass@host?a=b", None, None
        ) == {"DSN": "db://user:pass@host?a=b"}

    def test_value_without_an_assignment_fails_with_the_declared_format(self):
        with pytest.raises(
            click.UsageError, match=r'format must be "NAME=VALUE \[NAME2=VALUE2\]"'
        ):
            ContainerEnvironment().convert("DEBUG", None, None)

    def test_encoded_object_is_parsed_back(self):
        value = ContainerEnvironment.encode({"DEBUG": "1", "ENV": "local"})
        assert value == "DEBUG=1 ENV=local"
        assert ContainerEnvironment().convert(value, None, None) == {
            "DEBUG": "1",
            "ENV": "local",
        }

    def test_string_is_kept_as_is(self):
        assert ContainerEnvironment.encode("DEBUG=1") == "DEBUG=1"

    def test_variable_value_must_be_a_string(self):
        with pytest.raises(ValueError, match='"DEBUG" must be a string'):
            ContainerEnvironment.encode({"DEBUG": {"a": "b"}})
