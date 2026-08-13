import os
import re

import git
from click import BadParameter, UsageError
from git import GitCommandError, InvalidGitRepositoryError

from .types import ReleaseType, VersionFileType
from .version_utils import bump_to_next_version, bump_version, get_version

# Both quote styles are accepted: create_deployment_branch writes the branch name in single
# quotes, older deployment branches may still carry the double quoted form.
DEPLOYMENT_COMMIT_PATTERN = (
    r"^Deployment of (?P<quote>[\"'])(?P<branch_name>.+)(?P=quote)$"
)
# The optional "<prefix>@" (or "<prefix>/") group lets a package-prefixed tag like
# "habarico@1.3.0" resolve back to the bare version. Prefix-agnostic on purpose.
VERSION_PATTERN = r"^(?:.+[@/])?(?P<version>[0-9]+\.[0-9]+\.[0-9]+)$"


def _repo():
    # search_parent_directories lets pydev run from a subdirectory of a monorepo
    # (e.g. CI WORKDIR=packages/...), mirroring how the git CLI locates the repo root.
    return git.Repo(".", search_parent_directories=True)


def _release_prefix_part(release_prefix):
    # A non-empty prefix is joined to the version with "@"; empty/whitespace means no prefix,
    # keeping the historical naming untouched.
    if release_prefix and release_prefix.strip():
        return f"{release_prefix.strip()}@"
    return ""


def _release_branch_name(version, release_prefix=None):
    return "release/{}v{}.{}".format(
        _release_prefix_part(release_prefix), version.major, version.minor
    )


def _release_tag_name(version, release_prefix=None):
    return f"{_release_prefix_part(release_prefix)}{version}"


def create_release_branch(
    version, release_type, remote_name=None, branch_name=None, release_prefix=None
):
    repo = _repo()
    g = repo.git

    if branch_name:
        g.checkout(branch_name)
    if remote_name:
        g.pull(remote_name, branch_name)

    if release_type in {
        ReleaseType.minor,
        ReleaseType.major,
        ReleaseType.patch,
        ReleaseType.release,
    }:
        release_branch_name = _release_branch_name(version, release_prefix)
    else:
        raise BadParameter("build is not allowed for release")

    # The release branch may already be the checked out one (CI runs the release from it);
    # git refuses to create it again and standing on it is all that is needed.
    is_on_release_branch = (
        not repo.head.is_detached and repo.active_branch.name == release_branch_name
    )
    if not is_on_release_branch:
        g.checkout(branch_name or "HEAD", b=release_branch_name)

    if remote_name:
        g.push(remote_name, release_branch_name, force=True)
    return release_branch_name


def create_release(
    version_file,
    release_type,
    remote_name=None,
    branch_name=None,
    file_type=None,
    pre_release=None,
    release_prefix=None,
):
    repo = _repo()
    g = repo.git

    if branch_name:
        g.checkout(branch_name)

    bump_to_next_version(
        release_type, pre_release=pre_release, files=[version_file], file_type=file_type
    )
    version = get_version(version_file, file_type)

    # Add files by absolute path: g.add runs with cwd == git root, but the version
    # file may live in a subdirectory (monorepo WORKDIR) from which pydev was invoked.
    g.add(os.path.abspath(version_file))
    if file_type == VersionFileType.npm:
        lock_file = (
            f"{version_file.rsplit('.', 1)[0]}-lock.{version_file.rsplit('.', 1)[1]}"
        )
        g.add(os.path.abspath(lock_file))

    if remote_name and branch_name:
        g.pull(remote_name, branch_name)

    if release_type in {
        ReleaseType.minor,
        ReleaseType.major,
        ReleaseType.patch,
        ReleaseType.release,
    }:
        release_branch_name = _release_branch_name(version, release_prefix)
    else:
        raise BadParameter("build is not allowed for release")

    release_tag_name = _release_tag_name(version, release_prefix)

    # A patch release is usually built from the release branch itself (CI checks it out), so
    # the branch can be neither deleted nor recreated - the bump commit goes on top of it.
    is_on_release_branch = (
        not repo.head.is_detached and repo.active_branch.name == release_branch_name
    )

    branch_names = [branch.name for branch in repo.branches]
    if release_branch_name in branch_names and not is_on_release_branch:
        g.branch("-D", release_branch_name)

    tags = [tag.name for tag in repo.tags]
    if release_tag_name in tags:
        g.tag("-d", release_tag_name)

    if not is_on_release_branch:
        g.checkout(branch_name or "HEAD", b=release_branch_name)
    g.commit(message=f"Bump version to '{version}'")

    g.tag(release_tag_name)
    if remote_name:
        g.push(remote_name, release_branch_name)
        g.push(remote_name, release_tag_name)
    return release_branch_name


def create_branch(source_branch_name, new_branch_name):
    try:
        repo = _repo()
        g = repo.git

        g.checkout(source_branch_name, b=new_branch_name)
        return new_branch_name
    except GitCommandError:
        raise UsageError('Branch "{}" already exist'.format(new_branch_name))


def create_deployment_branch(environment, remote_name=None, is_hot=False):
    repo = _repo()
    g = repo.git
    source_branch_name = str(repo.head.reference)
    deployment_branch_name = "deploy-{}".format(environment)

    files_to_add = list(
        filter(None, (file for file in g.diff("--name-only", "--cached").split("\n")))
    )
    if files_to_add:
        g.stash("save")

    if is_hot:
        deployment_branch_name += "-hot"

    try:
        g.branch("-D", deployment_branch_name)
    except GitCommandError:
        # Branch not exits
        pass

    g.checkout("HEAD", b=deployment_branch_name)
    g.commit("--allow-empty", message="Deployment of '{}'".format(source_branch_name))

    if remote_name:
        g.push(remote_name, deployment_branch_name, force=True)

    g.checkout(source_branch_name)
    if files_to_add:
        g.stash("apply")
        g.add(files_to_add)
    return deployment_branch_name


def checkout_to_release_branch(remote_name=None):
    repo = _repo()
    g = repo.git
    match = re.match(DEPLOYMENT_COMMIT_PATTERN, repo.head.commit.message)
    if not match:
        raise UsageError("Invalid deployment branch commit")

    branch_name = match.group("branch_name")
    g.checkout(branch_name)
    if remote_name:
        g.pull(remote_name, branch_name)
    return branch_name


def bump_version_from_release_tag(files=["version.json"]):
    repo = _repo()

    g = repo.git

    tag = g.describe("--tags", "--exact-match")

    match = re.match(VERSION_PATTERN, str(tag))
    if not match:
        raise UsageError("Invalid release branch")
    bump_version(match.group("version"), files)
    return match.group("version")


def commit_version(
    version, files=["version.json"], remote_name=None, release_prefix=None
):
    repo = _repo()
    g = repo.git

    # In a monorepo the tag must carry the release prefix (e.g. "habarico@1.3.0"),
    # otherwise packages collide on the same bare "1.3.0" tag.
    tag_name = _release_tag_name(version, release_prefix)

    try:
        # Add files by absolute path: g.add runs with cwd == git root, but the version
        # files may live in a subdirectory (monorepo WORKDIR) from which pydev was invoked.
        g.add([os.path.abspath(f) for f in files])
        # Use the prefixed tag name so the merge bump commit reads
        # "Bump version to 'lib-a@1.3.0'" in a monorepo; with no prefix it stays "1.3.0".
        g.commit(m=f"Bump version to '{tag_name}'")
    except GitCommandError as ex:
        raise UsageError(
            "Version files was not changed or another git error was raised: {}".format(
                ex
            )
        )

    try:
        g.tag(tag_name)
    except GitCommandError as ex:
        raise UsageError(
            "Tag {} already exists or another git error was raised: {}".format(
                tag_name, ex
            )
        )

    if remote_name:
        g.push(remote_name, str(repo.head.reference))
        g.push(remote_name, tag_name)


def merge_release_branch(to_branch_name=None, remote_name=None):
    repo = _repo()
    g = repo.git
    source_branch_name = str(repo.head.reference)

    g.checkout(to_branch_name)
    if remote_name:
        g.pull(remote_name, to_branch_name)

    # GitPython does not support merge --no-ff or what?
    git_cmd = git.cmd.Git(".")
    no_ff_commit = f"Merge branch '{source_branch_name}'"
    git_cmd.execute(
        ("git", "merge", "--no-ff", "-m", no_ff_commit, str(source_branch_name))
    )

    if remote_name:
        g.push(remote_name, to_branch_name)

    g.checkout(source_branch_name)


def get_current_branch_name():
    repo = _repo()
    return str(repo.head.reference)


def get_commit_hash(branch_name):
    try:
        repo = _repo()
        return repo.heads[branch_name].object.hexsha
    except IndexError:
        raise UsageError("Invalid branch name: {}".format(branch_name))


def get_current_issue_key():
    branch_name = get_current_branch_name()
    match = re.match(r"(?P<issue_key>.{3}-\d+).*", branch_name)
    if match:
        return match.group("issue_key")
    else:
        return None


def get_remote_url():
    try:
        repo = _repo()
        url = repo.remotes.origin.url
        if url.startswith("git@"):
            return f"https://{url.split('@')[1].split(':', 1)[0]}"
        else:
            return f"https://{url.split('@')[1].split('/', 1)[0]}"
    except InvalidGitRepositoryError:
        raise UsageError("Git repository not found in the current directory")


def get_remote_path():
    try:
        repo = _repo()
        url = repo.remotes.origin.url
        if url.startswith("git@"):
            return url.split("@")[1].split(":", 1)[1].split(".")[0]
        else:
            return url.split("@")[1].split("/", 1)[1].split(".")[0]
    except InvalidGitRepositoryError:
        raise UsageError("Git repository not found in the current directory")
