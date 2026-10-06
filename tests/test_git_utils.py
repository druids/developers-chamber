import pytest
from click import UsageError

pytest.importorskip("git", reason='requires the "git" extra')

from developers_chamber.git_utils import (  # noqa: E402
    _release_branch_name,
    _release_prefix_part,
    _release_tag_name,
    bump_version_from_release_tag,
    checkout_to_release_branch,
    commit_version,
    create_branch,
    create_deployment_branch,
    create_release,
    create_release_branch,
    get_commit_hash,
    get_current_branch_name,
    get_current_issue_key,
    get_remote_path,
    get_remote_url,
)
from developers_chamber.types import ReleaseType  # noqa: E402
from developers_chamber.version_utils import Version  # noqa: E402

pytestmark = pytest.mark.usefixtures("git_repo")


class TestReleaseNames:
    """Names of the release branch and tag are pure, they need no repository."""

    @pytest.mark.parametrize("release_prefix", [None, "", "   "])
    def test_no_prefix_keeps_the_historical_naming(self, release_prefix):
        assert _release_prefix_part(release_prefix) == ""

    @pytest.mark.parametrize("release_prefix", ["habarico", "  habarico  "])
    def test_prefix_is_stripped_and_joined_with_an_at_sign(self, release_prefix):
        assert _release_prefix_part(release_prefix) == "habarico@"

    def test_branch_name_uses_the_major_and_the_minor_version(self):
        assert _release_branch_name(Version("1.2.3")) == "release/v1.2"

    def test_branch_name_carries_the_prefix(self):
        assert (
            _release_branch_name(Version("1.2.3"), "habarico")
            == "release/habarico@v1.2"
        )

    def test_tag_name_is_the_whole_version(self):
        assert _release_tag_name(Version("1.2.3")) == "1.2.3"

    @pytest.mark.parametrize(
        ("version", "expected"),
        [("1.2.3", "habarico@1.2.3"), ("1.2.3-beta.4", "habarico@1.2.3-beta.4")],
    )
    def test_tag_name_carries_the_prefix(self, version, expected):
        assert _release_tag_name(Version(version), "habarico") == expected


class TestBranch:

    def test_current_branch_name_is_returned(self):
        assert get_current_branch_name() == "master"

    def test_branch_is_created_and_checked_out(self):
        assert create_branch("master", "feature") == "feature"
        assert get_current_branch_name() == "feature"

    def test_existing_branch_is_reported(self):
        create_branch("master", "feature")
        with pytest.raises(UsageError, match='Branch "feature" already exist'):
            create_branch("master", "feature")

    def test_commit_hash_is_returned(self, git_repo):
        assert get_commit_hash("master") == git_repo.heads["master"].object.hexsha

    def test_unknown_branch_is_reported(self):
        with pytest.raises(UsageError, match="Invalid branch name: missing"):
            get_commit_hash("missing")

    def test_issue_key_is_read_from_the_branch_name(self):
        create_branch("master", "ABC-123-add-the-thing")
        assert get_current_issue_key() == "ABC-123"

    def test_branch_without_an_issue_key_returns_nothing(self):
        assert get_current_issue_key() is None


class TestCommitVersion:

    def test_version_files_are_committed_and_tagged(self, git_repo, version_file):
        version_file.write_version("1.3.0")
        commit_version("1.3.0")
        assert git_repo.head.commit.message.strip() == "Bump version to '1.3.0'"
        assert [str(tag) for tag in git_repo.tags] == ["1.3.0"]

    def test_tag_and_message_carry_the_release_prefix(self, git_repo, version_file):
        version_file.write_version("1.3.0")
        commit_version("1.3.0", release_prefix="habarico")
        assert (
            git_repo.head.commit.message.strip() == "Bump version to 'habarico@1.3.0'"
        )
        assert [str(tag) for tag in git_repo.tags] == ["habarico@1.3.0"]

    def test_tag_is_not_created_when_it_is_turned_off(self, git_repo, version_file):
        version_file.write_version("1.3.0")
        commit_version("1.3.0", release_prefix="habarico", tag=False)
        assert (
            git_repo.head.commit.message.strip() == "Bump version to 'habarico@1.3.0'"
        )
        assert git_repo.tags == []

    def test_existing_tag_does_not_block_a_commit_without_the_tag(
        self, git_repo, version_file
    ):
        git_repo.create_tag("1.3.0")
        version_file.write_version("1.3.0")
        commit_version("1.3.0", tag=False)
        assert git_repo.head.commit.message.strip() == "Bump version to '1.3.0'"

    def test_unchanged_version_files_are_reported(self):
        with pytest.raises(UsageError, match="Version files was not changed"):
            commit_version("1.3.0")

    def test_existing_tag_is_reported(self, git_repo, version_file):
        git_repo.create_tag("1.3.0")
        version_file.write_version("1.3.0")
        with pytest.raises(UsageError, match="Tag 1.3.0 already exists"):
            commit_version("1.3.0")


class TestBumpVersionFromReleaseTag:

    @pytest.mark.parametrize(
        "tag",
        ["2.0.0", "habarico@2.0.0", "habarico/2.0.0"],
        ids=["bare", "at", "slash"],
    )
    def test_version_is_taken_from_the_tag(self, git_repo, version_file, tag):
        git_repo.create_tag(tag)
        assert bump_version_from_release_tag() == "2.0.0"
        assert version_file.read_version() == "2.0.0"

    def test_tag_which_is_not_a_version_is_reported(self, git_repo):
        git_repo.create_tag("nightly")
        with pytest.raises(UsageError, match="Invalid release branch"):
            bump_version_from_release_tag()


class TestCreateReleaseBranch:

    def test_branch_is_created_from_the_current_branch(self, git_repo):
        assert (
            create_release_branch(Version("1.3.0"), ReleaseType.minor) == "release/v1.3"
        )
        assert git_repo.active_branch.name == "release/v1.3"

    def test_checked_out_release_branch_is_kept(self, git_repo):
        """The branch cannot be created again while the worktree stands on it."""
        git_repo.git.checkout("HEAD", b="release/v1.2")
        assert (
            create_release_branch(Version("1.2.4"), ReleaseType.patch) == "release/v1.2"
        )
        assert git_repo.active_branch.name == "release/v1.2"


class TestCreateRelease:

    def test_release_branch_is_created_from_the_current_branch(self, git_repo):
        assert create_release("version.json", ReleaseType.minor) == "release/v1.3"
        assert git_repo.active_branch.name == "release/v1.3"
        assert git_repo.head.commit.message.strip() == "Bump version to '1.3.0'"
        assert "1.3.0" in [tag.name for tag in git_repo.tags]

    def test_existing_release_branch_is_replaced(self, git_repo):
        git_repo.git.branch("release/v1.3")
        assert create_release("version.json", ReleaseType.minor) == "release/v1.3"
        assert git_repo.head.commit.message.strip() == "Bump version to '1.3.0'"

    def test_release_is_committed_on_top_of_the_checked_out_release_branch(
        self, git_repo
    ):
        """The release branch cannot be deleted while the worktree stands on it."""
        git_repo.git.checkout("HEAD", b="release/v1.2")
        assert create_release("version.json", ReleaseType.patch) == "release/v1.2"
        assert git_repo.active_branch.name == "release/v1.2"
        assert git_repo.head.commit.message.strip() == "Bump version to '1.2.4'"
        assert "1.2.4" in [tag.name for tag in git_repo.tags]


class TestDeploymentBranch:

    def test_deployment_branch_is_created_and_the_source_branch_restored(
        self, git_repo
    ):
        assert create_deployment_branch("test") == "deploy-test"
        assert get_current_branch_name() == "master"
        assert "deploy-test" in [head.name for head in git_repo.heads]

    def test_hot_deployment_branch_has_its_own_name(self):
        assert create_deployment_branch("test", is_hot=True) == "deploy-test-hot"

    def test_existing_deployment_branch_is_replaced_instead_of_stacked(self, git_repo):
        create_deployment_branch("test")
        create_deployment_branch("test")
        deployment_commit = git_repo.heads["deploy-test"].commit
        assert [parent.hexsha for parent in deployment_commit.parents] == [
            git_repo.heads["master"].commit.hexsha
        ]

    def test_release_branch_is_read_back_from_the_deployment_commit(self, git_repo):
        create_branch("master", "release/v1.2")
        create_deployment_branch("test")
        git_repo.git.checkout("deploy-test")
        assert checkout_to_release_branch() == "release/v1.2"
        assert get_current_branch_name() == "release/v1.2"

    def test_double_quoted_deployment_commit_is_still_read(self, git_repo):
        # the form written by the older versions of pydev
        create_branch("master", "release/v1.2")
        git_repo.git.checkout("HEAD", b="deploy-old")
        git_repo.git.commit("--allow-empty", message='Deployment of "release/v1.2"')
        assert checkout_to_release_branch() == "release/v1.2"

    def test_commit_which_is_not_a_deployment_is_reported(self):
        with pytest.raises(UsageError, match="Invalid deployment branch commit"):
            checkout_to_release_branch()


class TestRemote:

    def test_ssh_remote_is_split_into_a_url_and_a_path(self, git_repo):
        git_repo.create_remote("origin", "git@github.com:druids/developers-chamber.git")
        assert get_remote_url() == "https://github.com"
        assert get_remote_path() == "druids/developers-chamber"

    def test_https_remote_with_credentials_is_split(self, git_repo):
        git_repo.create_remote(
            "origin", "https://oauth2:token@gitlab.example.com/group/project.git"
        )
        assert get_remote_url() == "https://gitlab.example.com"
        assert get_remote_path() == "group/project"
