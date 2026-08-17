import pytest
from click import UsageError

from developers_chamber import gitlab_utils
from developers_chamber.gitlab_utils import (
    _auth_headers,
    _release_record_name,
    create_release_record,
    parse_asset_links,
)


class TestAuthHeaders:
    """The Releases API takes a job token, the rest of the API takes a private one."""

    def test_private_token_is_sent_in_the_private_token_header(self):
        assert _auth_headers(token="secret") == {"PRIVATE-TOKEN": "secret"}

    def test_job_token_is_sent_in_the_job_token_header(self):
        assert _auth_headers(job_token="ci-secret") == {"JOB-TOKEN": "ci-secret"}

    def test_job_token_wins_over_the_private_one(self):
        assert _auth_headers(token="secret", job_token="ci-secret") == {
            "JOB-TOKEN": "ci-secret"
        }

    def test_missing_token_is_reported(self):
        with pytest.raises(UsageError, match="token"):
            _auth_headers()


class TestReleaseRecordName:
    """The release is named after its tag, the monorepo prefix included."""

    def test_tag_without_a_prefix_is_the_name(self):
        assert _release_record_name("1.3.0") == "1.3.0"

    def test_prefix_is_separated_from_the_version_by_a_space(self):
        assert _release_record_name("lib-a@1.3.0") == "lib-a 1.3.0"

    def test_pre_release_tag_keeps_its_suffix(self):
        assert _release_record_name("lib-a@1.3.0-beta.4") == "lib-a 1.3.0-beta.4"


class TestParseAssetLinks:
    def test_no_asset_gives_no_link(self):
        assert parse_asset_links(()) == []

    def test_asset_is_split_into_a_name_and_a_url(self):
        assert parse_asset_links(("Wheel=https://pypi.example.com/pkg.whl",)) == [
            {"name": "Wheel", "url": "https://pypi.example.com/pkg.whl"}
        ]

    def test_assets_keep_their_order(self):
        assert parse_asset_links(("a=https://x", "b=https://y")) == [
            {"name": "a", "url": "https://x"},
            {"name": "b", "url": "https://y"},
        ]

    def test_url_query_string_survives_the_split(self):
        assert parse_asset_links(("Image=https://reg.example.com/i?tag=1.3.0",)) == [
            {"name": "Image", "url": "https://reg.example.com/i?tag=1.3.0"}
        ]

    @pytest.mark.parametrize("asset", ["https://x", "=https://x", "name=", "name"])
    def test_malformed_asset_is_reported(self, asset):
        with pytest.raises(UsageError, match="name=URL"):
            parse_asset_links((asset,))


class FakeResponse:
    def __init__(self, status_code=201, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.content = b'{"message": "error"}'

    def json(self):
        return self._payload


@pytest.fixture
def post(monkeypatch):
    """Catch the request instead of sending it, and answer it with a created release."""

    calls = []

    def fake_post(url, headers=None, json=None):
        calls.append({"url": url, "headers": headers, "json": json})
        return fake_post.response

    fake_post.response = FakeResponse(
        payload={
            "_links": {
                "self": "https://gitlab.example.com/g/p/-/releases/lib-a%401.3.0"
            }
        }
    )
    fake_post.calls = calls
    monkeypatch.setattr(gitlab_utils.requests, "post", fake_post)
    return fake_post


class TestCreateReleaseRecord:
    def test_release_is_posted_to_the_project_releases_endpoint(self, post):
        create_release_record(
            url="https://gitlab.example.com",
            project="group/project",
            tag_name="1.3.0",
            token="secret",
        )

        assert (
            post.calls[0]["url"]
            == "https://gitlab.example.com/api/v4/projects/group%2Fproject/releases"
        )

    def test_numeric_project_id_is_used_as_it_is(self, post):
        create_release_record(
            url="https://gitlab.example.com",
            project="42",
            tag_name="1.3.0",
            token="secret",
        )

        assert post.calls[0]["url"].endswith("/projects/42/releases")

    def test_job_token_is_used_for_the_call(self, post):
        create_release_record(
            url="https://gitlab.example.com",
            project="group/project",
            tag_name="1.3.0",
            token="secret",
            job_token="ci-secret",
        )

        assert post.calls[0]["headers"] == {"JOB-TOKEN": "ci-secret"}

    def test_name_defaults_to_the_tag(self, post):
        create_release_record(
            url="https://gitlab.example.com",
            project="group/project",
            tag_name="lib-a@1.3.0",
            token="secret",
        )

        assert post.calls[0]["json"] == {
            "tag_name": "lib-a@1.3.0",
            "name": "lib-a 1.3.0",
        }

    def test_given_name_and_description_are_sent(self, post):
        create_release_record(
            url="https://gitlab.example.com",
            project="group/project",
            tag_name="1.3.0",
            name="Chamber 1.3.0",
            description="### Added\n- a thing",
            token="secret",
        )

        assert post.calls[0]["json"] == {
            "tag_name": "1.3.0",
            "name": "Chamber 1.3.0",
            "description": "### Added\n- a thing",
        }

    def test_empty_description_is_left_out(self, post):
        create_release_record(
            url="https://gitlab.example.com",
            project="group/project",
            tag_name="1.3.0",
            description="",
            token="secret",
        )

        assert "description" not in post.calls[0]["json"]

    def test_asset_links_are_sent_as_release_assets(self, post):
        create_release_record(
            url="https://gitlab.example.com",
            project="group/project",
            tag_name="1.3.0",
            asset_links=[{"name": "Wheel", "url": "https://pypi.example.com/pkg.whl"}],
            token="secret",
        )

        assert post.calls[0]["json"]["assets"] == {
            "links": [{"name": "Wheel", "url": "https://pypi.example.com/pkg.whl"}]
        }

    def test_no_asset_link_leaves_the_assets_out(self, post):
        create_release_record(
            url="https://gitlab.example.com",
            project="group/project",
            tag_name="1.3.0",
            asset_links=[],
            token="secret",
        )

        assert "assets" not in post.calls[0]["json"]

    def test_web_url_of_the_release_is_returned(self, post):
        assert (
            create_release_record(
                url="https://gitlab.example.com",
                project="group/project",
                tag_name="lib-a@1.3.0",
                token="secret",
            )
            == "https://gitlab.example.com/g/p/-/releases/lib-a%401.3.0"
        )

    def test_answer_without_a_link_falls_back_to_the_tag(self, post):
        post.response = FakeResponse(payload={})

        assert (
            create_release_record(
                url="https://gitlab.example.com",
                project="group/project",
                tag_name="lib-a@1.3.0",
                token="secret",
            )
            == "lib-a@1.3.0"
        )

    def test_rejected_call_is_reported(self, post):
        post.response = FakeResponse(status_code=409)

        with pytest.raises(UsageError, match="GitLab error"):
            create_release_record(
                url="https://gitlab.example.com",
                project="group/project",
                tag_name="1.3.0",
                token="secret",
            )
