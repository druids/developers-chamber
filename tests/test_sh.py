import pytest
from click.testing import CliRunner

import developers_chamber.scripts.sh as sh_module
from developers_chamber.scripts import cli
from developers_chamber.scripts.sh import sh  # noqa: F401  registers the command


@pytest.fixture
def run_sh(monkeypatch):
    """Runs the sh command and returns what it would hand over to the shell."""
    commands = []
    monkeypatch.setattr(
        sh_module, "call_command", lambda command, **kwargs: commands.append(command)
    )

    def run(*args):
        result = CliRunner().invoke(cli, ["sh", *args], standalone_mode=False)
        if result.exit_code:
            raise AssertionError(result.output.strip() or repr(result.exception))
        return commands[-1]

    return run


def test_quoted_command_is_passed_as_it_is(run_sh):
    assert run_sh("python script.py") == "python script.py"


@pytest.mark.parametrize(
    "command",
    [
        "python a.py && python b.py",
        "python a.py; python b.py",
        "python a.py | tee log.txt",
        "python a.py > log.txt",
    ],
    ids=["and", "semicolon", "pipe", "redirect"],
)
def test_shell_operators_of_a_quoted_command_are_kept(run_sh, command):
    assert run_sh(command) == command


def test_rest_of_the_command_line_is_joined_back(run_sh):
    assert run_sh("python", "script.py") == "python script.py"


def test_options_of_the_command_are_not_parsed_by_pydev(run_sh):
    assert (
        run_sh("python", "manage.py", "migrate", "--no-input")
        == "python manage.py migrate --no-input"
    )


def test_quoting_of_the_joined_arguments_is_kept(run_sh):
    assert run_sh("python", "-c", "print('x')") == "python -c 'print('\"'\"'x'\"'\"')'"


def test_argument_with_a_space_stays_one_argument(run_sh):
    assert run_sh("grep", "a b", "file.txt") == "grep 'a b' file.txt"


def test_shell_operator_given_as_its_own_argument_stays_a_plain_argument(run_sh):
    # a shell operator is only an operator inside a quoted command, several arguments are an
    # argument vector where it has no special meaning
    assert run_sh("echo", "a;", "echo", "b") == "echo 'a;' echo b"


def test_missing_command_is_reported(monkeypatch):
    commands = []
    monkeypatch.setattr(
        sh_module, "call_command", lambda command, **kwargs: commands.append(command)
    )
    result = CliRunner().invoke(cli, ["sh"], standalone_mode=False)
    assert result.exit_code != 0
    assert commands == []
