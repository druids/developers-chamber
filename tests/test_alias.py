import pytest

from developers_chamber.click.alias import find_and_replace_command_variable


@pytest.mark.parametrize(
    ("arg", "command", "index", "expected"),
    [
        (
            "--app=users",
            "project run './manage.py migrate $app'",
            1,
            (True, "project run './manage.py migrate users'"),
        ),
        ("--app users", "project run '$app'", 1, (True, "project run 'users'")),
        (
            "--app-name=users",
            "project run '$app_name'",
            1,
            (True, "project run 'users'"),
        ),
        ("users", "project run '$1'", 1, (True, "project run 'users'")),
        ("users", "project run '$1'", 2, (False, "project run '$1'")),
        ("--other=users", "project run '$app'", 1, (False, "project run '$app'")),
        ("--app=users", "project run '$1'", 1, (True, "project run '--app=users'")),
    ],
    ids=[
        "named argument",
        "named argument separated by a space",
        "dashes match an underscore variable",
        "positional argument",
        "index is respected",
        "unknown name is left for the command",
        "named argument falls back to its index",
    ],
)
def test_command_variable_is_replaced(arg, command, index, expected):
    assert find_and_replace_command_variable(arg, command, index) == expected
