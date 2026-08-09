import pytest
from click import ClickException

from developers_chamber.utils import call_command, pretty_time_delta, remove_ansi


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (45, "45s"),
        (125, "2m 5s"),
        (3725, "1h 2m 5s"),
        (0, "0s"),
        (-125, "2m 5s"),
        (45.9, "45s"),
    ],
    ids=["seconds", "minutes", "hours", "zero", "negative", "fraction"],
)
def test_time_delta_is_rendered(seconds, expected):
    assert pretty_time_delta(seconds) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("\x1b[31mfailed\x1b[0m", "failed"),
        ("failed", "failed"),
        ("\x1b[31ma\nb\x1b[0m", "a\nb"),
    ],
    ids=["color sequence", "plain text", "newlines kept"],
)
def test_ansi_is_removed(value, expected):
    assert remove_ansi(value) == expected


def test_successful_command_returns():
    assert call_command("exit 0", quiet=True) is None


def test_failed_command_is_reported():
    with pytest.raises(ClickException, match="Command returned error"):
        call_command("exit 1", quiet=True)


def test_command_given_as_a_list_is_run_without_a_shell():
    assert call_command(["true"], quiet=True) is None


def test_environment_is_passed_to_the_command():
    assert (
        call_command('[ "$PYDEV_TEST" = "1" ]', quiet=True, env={"PYDEV_TEST": "1"})
        is None
    )


def test_command_without_the_environment_does_not_see_it():
    with pytest.raises(ClickException):
        call_command('[ "$PYDEV_TEST" = "1" ]', quiet=True)
