from datetime import timedelta

import click
import pytest

from developers_chamber.types import (
    EnumType,
    PreReleaseType,
    ReleaseType,
    TimedeltaType,
    VersionFileType,
)


def convert_timedelta(value):
    return TimedeltaType().convert(value, None, None)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2", timedelta(hours=2)),
        ("30s", timedelta(seconds=30)),
        ("15m", timedelta(minutes=15)),
        ("3h", timedelta(hours=3)),
        ("1d", timedelta(hours=8)),
        ("1h30m", timedelta(hours=1, minutes=30)),
        (" 1h 30m ", timedelta(hours=1, minutes=30)),
    ],
    ids=[
        "hours by default",
        "seconds",
        "minutes",
        "hours",
        "working day",
        "sum",
        "whitespace",
    ],
)
def test_time_delta_is_parsed(value, expected):
    assert convert_timedelta(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("30m2", timedelta(minutes=30, hours=2)), ("1h30", timedelta(hours=31))],
)
def test_trailing_number_is_added_to_the_preceding_units(value, expected):
    # a trailing number has no unit of its own and falls back to hours
    assert convert_timedelta(value) == expected


def test_unknown_unit_is_rejected():
    with pytest.raises(click.UsageError, match="Invalid time delta"):
        convert_timedelta("5x")


def test_enum_name_is_converted_to_the_member():
    assert EnumType(ReleaseType).convert("minor", None, None) is ReleaseType.minor


def test_unknown_enum_name_is_rejected():
    with pytest.raises(click.UsageError):
        EnumType(ReleaseType).convert("revision", None, None)


def test_enum_choices_are_the_members():
    assert list(EnumType(PreReleaseType).choices) == ["alpha", "beta", "rc"]


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (ReleaseType.build, "build"),
        (PreReleaseType.rc, "rc"),
        (VersionFileType.npm, "npm"),
    ],
)
def test_enum_is_rendered_as_its_value(member, expected):
    assert str(member) == expected


def test_version_file_type_compares_to_its_value():
    # the file type is resolved from a file extension, therefore it has to be a string
    assert VersionFileType.toml == "toml"
