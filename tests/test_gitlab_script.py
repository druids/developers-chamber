import pytest
from click.testing import CliRunner

pytest.importorskip("git", reason='requires the "gitlab" extra')

from developers_chamber.scripts import gitlab as gitlab_script  # noqa: E402

AMBIENT_ENVVARS = (
    "GITLAB_URL",
    "GITLAB_API_URL",
    "GITLAB_TOKEN",
    "GITLAB_PROJECT",
    "CI_JOB_TOKEN",
    "CI_COMMIT_TAG",
)


@pytest.fixture
def create_release_record(monkeypatch):
    """Catch what the command hands over to the API call."""

    calls = []

    def fake_create_release_record(**kwargs):
        calls.append(kwargs)
        return "https://gitlab.example.com/g/p/-/releases/1.3.0"

    fake_create_release_record.calls = calls
    monkeypatch.setattr(
        gitlab_script, "create_release_record_func", fake_create_release_record
    )
    return fake_create_release_record


def run(args, env=None):
    return CliRunner().invoke(
        gitlab_script.create_release_record,
        args,
        # The variables of the developer environment must not decide the result of a test.
        env={**{name: None for name in AMBIENT_ENVVARS}, **(env or {})},
    )


class TestCreateReleaseRecordCommand:
    def test_tag_name_is_required(self, create_release_record):
        result = run(["--url", "https://gitlab.example.com", "--token", "secret"])

        assert result.exit_code != 0
        assert "--tag-name" in result.output

    def test_a_token_is_required(self, create_release_record):
        result = run(
            [
                "--url",
                "https://gitlab.example.com",
                "--project",
                "group/project",
                "--tag-name",
                "1.3.0",
            ]
        )

        assert result.exit_code != 0
        assert "token" in result.output

    def test_release_is_created_from_the_options(self, create_release_record):
        result = run(
            [
                "--url",
                "https://gitlab.example.com",
                "--project",
                "group/project",
                "--token",
                "secret",
                "--tag-name",
                "lib-a@1.3.0",
                "--description",
                "### Added\n- a thing",
            ]
        )

        assert result.exit_code == 0, result.output
        assert create_release_record.calls[0] == {
            "url": "https://gitlab.example.com",
            "project": "group/project",
            "tag_name": "lib-a@1.3.0",
            "name": None,
            "description": "### Added\n- a thing",
            "asset_links": [],
            "token": "secret",
            "job_token": None,
        }

    def test_job_token_is_taken_from_the_ci_environment(self, create_release_record):
        result = run(
            [
                "--url",
                "https://gitlab.example.com",
                "--project",
                "group/project",
                "--tag-name",
                "1.3.0",
            ],
            env={"CI_JOB_TOKEN": "ci-secret"},
        )

        assert result.exit_code == 0, result.output
        assert create_release_record.calls[0]["job_token"] == "ci-secret"

    def test_tag_name_is_taken_from_the_ci_environment(self, create_release_record):
        result = run(
            [
                "--url",
                "https://gitlab.example.com",
                "--project",
                "group/project",
                "--token",
                "secret",
            ],
            env={"CI_COMMIT_TAG": "lib-a@1.3.0"},
        )

        assert result.exit_code == 0, result.output
        assert create_release_record.calls[0]["tag_name"] == "lib-a@1.3.0"

    def test_assets_are_repeatable(self, create_release_record):
        result = run(
            [
                "--url",
                "https://gitlab.example.com",
                "--project",
                "group/project",
                "--token",
                "secret",
                "--tag-name",
                "1.3.0",
                "--asset",
                "Wheel=https://pypi.example.com/pkg.whl",
                "--asset",
                "Image=https://reg.example.com/i?tag=1.3.0",
            ]
        )

        assert result.exit_code == 0, result.output
        assert create_release_record.calls[0]["asset_links"] == [
            {"name": "Wheel", "url": "https://pypi.example.com/pkg.whl"},
            {"name": "Image", "url": "https://reg.example.com/i?tag=1.3.0"},
        ]

    def test_malformed_asset_stops_the_command(self, create_release_record):
        result = run(
            [
                "--url",
                "https://gitlab.example.com",
                "--project",
                "group/project",
                "--token",
                "secret",
                "--tag-name",
                "1.3.0",
                "--asset",
                "https://pypi.example.com/pkg.whl",
            ]
        )

        assert result.exit_code != 0
        assert "name=URL" in result.output
        assert create_release_record.calls == []

    def test_project_falls_back_to_the_git_remote(
        self, create_release_record, monkeypatch
    ):
        monkeypatch.setattr(
            gitlab_script, "get_remote_path", lambda: "group/from-remote"
        )

        result = run(
            [
                "--url",
                "https://gitlab.example.com",
                "--token",
                "secret",
                "--tag-name",
                "1.3.0",
            ]
        )

        assert result.exit_code == 0, result.output
        assert create_release_record.calls[0]["project"] == "group/from-remote"

    def test_created_release_is_reported(self, create_release_record):
        result = run(
            [
                "--url",
                "https://gitlab.example.com",
                "--project",
                "group/project",
                "--token",
                "secret",
                "--tag-name",
                "1.3.0",
            ]
        )

        assert result.exit_code == 0, result.output
        assert (
            "Release record was successfully created: "
            "https://gitlab.example.com/g/p/-/releases/1.3.0" in result.output
        )
