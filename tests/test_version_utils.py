import json

import pytest
import toml
from click import BadParameter

from developers_chamber.types import PreReleaseType, ReleaseType, VersionFileType
from developers_chamber.version_utils import (
    InvalidVersion,
    Version,
    _resolve_file_type,
    bump_to_next_version,
    bump_version,
    get_next_version,
    get_version,
    get_version_files,
    read_version_from_pom,
)

POM = """<?xml version="1.0" encoding="utf-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <artifactId>example</artifactId>
  <version>{}</version>
</project>
"""


class TestVersion:

    def test_full_version_is_parsed(self):
        version = Version("1.2.3")
        assert (version.major, version.minor, version.patch) == (1, 2, 3)
        assert version.pre_release is None
        assert version.build is None

    def test_missing_patch_defaults_to_zero(self):
        assert str(Version("1.2")) == "1.2.0"

    def test_pre_release_is_parsed(self):
        version = Version("1.2.3-beta.4")
        assert (version.pre_release, version.pre_release_num) == ("beta", 4)
        assert version.build is None

    def test_build_is_parsed(self):
        version = Version("1.2.3-abc12")
        assert version.build == "abc12"
        assert version.pre_release is None

    def test_pre_release_without_a_number_is_a_build(self):
        # the pre-release alternative of the pattern requires the number, so a bare stage name
        # falls through to the build alternative
        version = Version("1.2.3-beta")
        assert version.build == "beta"
        assert version.pre_release is None

    @pytest.mark.parametrize("version_str", ["1.2.3", "1.2.3-beta.4", "1.2.3-abc12"])
    def test_version_is_rendered_back_to_the_same_string(self, version_str):
        assert str(Version(version_str)) == version_str

    @pytest.mark.parametrize(
        "version_str", ["", "1", "1.2.3.4", "v1.2.3", "1.2.3-beta.x"]
    )
    def test_invalid_version_is_rejected(self, version_str):
        with pytest.raises(InvalidVersion):
            Version(version_str)

    def test_replace_changes_only_the_given_parts(self):
        assert str(Version("1.2.3").replace(minor=5)) == "1.5.3"

    def test_replace_rejects_an_unknown_part(self):
        with pytest.raises(AssertionError):
            Version("1.2.3").replace(revision=1)


class TestResolveFileType:

    def test_explicit_file_type_wins(self):
        assert _resolve_file_type(VersionFileType.npm, ".json") is VersionFileType.npm

    def test_file_type_is_detected_from_the_extension(self):
        assert _resolve_file_type(None, ".toml") == "toml"

    def test_file_without_an_extension_is_a_text_file(self):
        assert _resolve_file_type(None, "") is VersionFileType.text


class TestGetVersion:

    @pytest.mark.parametrize(
        ("name", "content"),
        [
            ("version.json", json.dumps({"version": "1.2.3"})),
            ("pyproject.toml", toml.dumps({"project": {"version": "1.2.3"}})),
            ("VERSION", "1.2.3\n"),
            ("pom.xml", POM.format("1.2.3")),
        ],
        ids=["json", "toml", "text without an extension", "pom"],
    )
    def test_version_is_read(self, version_file, name, content):
        version_file.write(name, content)
        assert str(get_version(name)) == "1.2.3"

    def test_missing_file_is_reported(self, project_dir):
        with pytest.raises(BadParameter, match="was not found"):
            get_version("version.json")


class TestGetVersionFiles:

    def test_only_the_file_itself_is_returned_by_default(self, project_dir):
        assert get_version_files("version.json") == ["version.json"]

    def test_existing_npm_lock_file_is_added(self, version_file):
        version_file.write("package.json", "{}")
        version_file.write("package-lock.json", "{}")
        assert get_version_files("package.json", VersionFileType.npm) == [
            "package.json",
            "package-lock.json",
        ]

    def test_missing_npm_lock_file_is_left_out(self, version_file):
        version_file.write("package.json", "{}")
        assert get_version_files("package.json", VersionFileType.npm) == [
            "package.json"
        ]


class TestBumpVersion:

    def test_json_file_keeps_its_other_keys(self, version_file):
        version_file.write(
            "version.json", json.dumps({"name": "example", "version": "1.2.3"})
        )
        bump_version("2.0.0", ["version.json"])
        assert json.loads((version_file.path / "version.json").read_text()) == {
            "name": "example",
            "version": "2.0.0",
        }

    def test_toml_file_is_bumped(self, version_file):
        version_file.write(
            "pyproject.toml", toml.dumps({"project": {"name": "e", "version": "1.2.3"}})
        )
        bump_version("2.0.0", ["pyproject.toml"])
        assert toml.loads((version_file.path / "pyproject.toml").read_text())[
            "project"
        ] == {
            "name": "e",
            "version": "2.0.0",
        }

    def test_text_file_is_bumped(self, version_file):
        version_file.write("VERSION", "1.2.3")
        bump_version("2.0.0", ["VERSION"])
        assert (version_file.path / "VERSION").read_text() == "2.0.0"

    def test_pom_file_is_bumped(self, version_file):
        version_file.write("pom.xml", POM.format("1.2.3"))
        bump_version("2.0.0", ["pom.xml"])
        assert read_version_from_pom() == "2.0.0"

    def test_npm_file_is_bumped_together_with_its_lock_file(self, version_file):
        version_file.write_version("1.2.3", "package.json")
        version_file.write(
            "package-lock.json",
            json.dumps({"version": "1.2.3", "packages": {"": {"version": "1.2.3"}}}),
        )
        bump_version("2.0.0", ["package.json"], VersionFileType.npm)
        assert version_file.read_version("package.json") == "2.0.0"
        lock_data = json.loads((version_file.path / "package-lock.json").read_text())
        assert lock_data["version"] == "2.0.0"
        assert lock_data["packages"][""]["version"] == "2.0.0"

    def test_missing_npm_lock_file_is_reported(self, version_file):
        version_file.write_version("1.2.3", "package.json")
        with pytest.raises(BadParameter, match="Lock file .* was not found"):
            bump_version("2.0.0", ["package.json"], VersionFileType.npm)

    def test_all_given_files_are_bumped(self, version_file):
        version_file.write_version("1.2.3")
        version_file.write("VERSION", "1.2.3")
        bump_version("2.0.0", ["version.json", "VERSION"])
        assert version_file.read_version() == "2.0.0"
        assert (version_file.path / "VERSION").read_text() == "2.0.0"

    def test_missing_file_is_reported(self, project_dir):
        with pytest.raises(BadParameter, match="was not found"):
            bump_version("2.0.0", ["version.json"])

    def test_no_files_is_reported(self, project_dir):
        with pytest.raises(BadParameter, match="Given no files"):
            bump_version("2.0.0", [])


class TestGetNextVersion:

    @pytest.fixture
    def next_version(self, version_file):
        def get(current, **kwargs):
            version_file.write_version(current)
            return str(get_next_version(file="version.json", **kwargs))

        return get

    @pytest.mark.parametrize(
        ("current", "kwargs", "expected"),
        [
            ("1.2.3", {"release_type": ReleaseType.patch}, "1.2.4"),
            ("1.2.3", {"release_type": ReleaseType.minor}, "1.3.0"),
            ("1.2.3", {"release_type": ReleaseType.major}, "2.0.0"),
            ("1.2.3", {}, "2.0.0"),
            ("1.2.3-beta.4", {"release_type": ReleaseType.patch}, "1.2.4"),
            ("1.2.3-beta.4", {"release_type": ReleaseType.release}, "1.2.3"),
            (
                "1.2.3",
                {"release_type": ReleaseType.build, "build_hash": "abcdef123456"},
                "1.2.3-abcde",
            ),
        ],
        ids=[
            "patch",
            "minor resets the patch",
            "major resets the rest",
            "no release type bumps the major",
            "bump drops the pre-release",
            "release only drops the pre-release",
            "build hash is shortened",
        ],
    )
    def test_version_is_bumped(self, next_version, current, kwargs, expected):
        assert next_version(current, **kwargs) == expected

    def test_build_without_a_hash_is_reported(self, next_version):
        with pytest.raises(BadParameter, match="Build hash is required"):
            next_version("1.2.3", release_type=ReleaseType.build)

    @pytest.mark.parametrize(
        ("current", "kwargs", "expected"),
        [
            ("1.2.3-alpha.1", {"pre_release": PreReleaseType.alpha}, "1.2.3-alpha.2"),
            ("1.2.3-alpha.2", {"pre_release": PreReleaseType.beta}, "1.2.3-beta.1"),
            (
                "1.2.3",
                {
                    "release_type": ReleaseType.minor,
                    "pre_release": PreReleaseType.alpha,
                },
                "1.3.0-alpha.1",
            ),
            (
                "1.2.3",
                {"release_type": ReleaseType.major, "pre_release": PreReleaseType.beta},
                "2.0.0-beta.1",
            ),
        ],
        ids=[
            "same stage increments its number",
            "higher stage starts from one",
            "minor release starts a new pre-release",
            "major release starts a new pre-release",
        ],
    )
    def test_pre_release_is_bumped(self, next_version, current, kwargs, expected):
        assert next_version(current, **kwargs) == expected

    @pytest.mark.parametrize(
        ("current", "kwargs", "message"),
        [
            (
                "1.2.3-rc.1",
                {"pre_release": PreReleaseType.alpha},
                "Cannot downgrade pre-release stage",
            ),
            (
                "1.2.3",
                {"pre_release": PreReleaseType.alpha},
                "without specifying --release-type",
            ),
            (
                "1.2.3-alpha.1",
                {
                    "release_type": ReleaseType.patch,
                    "pre_release": PreReleaseType.alpha,
                },
                "not allowed for patch releases",
            ),
        ],
        ids=["downgrade", "stable version without a release type", "patch release"],
    )
    def test_invalid_pre_release_is_reported(
        self, next_version, current, kwargs, message
    ):
        with pytest.raises(BadParameter, match=message):
            next_version(current, **kwargs)


class TestBumpToNextVersion:

    def test_next_version_is_written_to_all_files(self, version_file):
        version_file.write_version("1.2.3")
        version_file.write("VERSION", "1.2.3")
        bump_to_next_version(
            release_type=ReleaseType.minor, files=["version.json", "VERSION"]
        )
        assert version_file.read_version() == "1.3.0"
        assert (version_file.path / "VERSION").read_text() == "1.3.0"

    def test_no_files_is_reported(self, project_dir):
        with pytest.raises(BadParameter, match="Given no files"):
            bump_to_next_version(release_type=ReleaseType.minor, files=[])


class TestReadVersionFromPom:

    def test_version_is_read(self, version_file):
        version_file.write("pom.xml", POM.format("1.2.3"))
        assert read_version_from_pom() == "1.2.3"

    def test_missing_file_is_reported(self, project_dir):
        with pytest.raises(BadParameter, match="was not found"):
            read_version_from_pom()
