import re

import git
from click import BadParameter, UsageError
from git import GitCommandError

from .types import ReleaseType
from .version_utils import bump_version

DEPLOYMENT_COMMIT_PATTERN = r'^Deployment of "(?P<branch_name>.+)"$'
RELEASE_BRANCH_PATTERN = r'^(?P<release_type>(release|patch))-(?P<version>[0-9]+\.[0-9]+\.[0-9]+)$'


def create_release_branch(version, release_type, remote_name=None, branch_name=None):
    repo = git.Repo('.')
    g = repo.git

    if branch_name:
        g.checkout(branch_name)
    if remote_name:
        g.pull(remote_name, branch_name)

    if release_type in {ReleaseType.minor, ReleaseType.major}:
        release_branch_name = 'release-{}'.format(version)
    elif release_type == ReleaseType.patch:
        release_branch_name = 'patch-{}'.format(version)
    else:
        raise BadParameter('build is not allowed for release')
    g.checkout(branch_name or 'HEAD', b=release_branch_name)

    if remote_name:
        g.push(remote_name, release_branch_name, force=True)
    return release_branch_name


def create_branch(source_branch_name, new_branch_name):
    try:
        repo = git.Repo('.')
        g = repo.git

        g.checkout(source_branch_name, b=new_branch_name)
        return new_branch_name
    except GitCommandError:
        raise UsageError('Branch "{}" already exist'.format(new_branch_name))


def create_deployment_branch(environment, remote_name=None, is_hot=False):
    repo = git.Repo('.')
    g = repo.git
    source_branch_name = str(repo.head.reference)
    deployment_branch_name = 'deploy-{}'.format(environment)

    if is_hot:
        deployment_branch_name += '-hot'

    try:
        g.branch('-D', deployment_branch_name)
    except GitCommandError:
        # Branch not exits
        pass

    g.checkout('HEAD', b=deployment_branch_name)
    g.commit('--allow-empty', message='Deployment of "{}"'.format(source_branch_name))

    if remote_name:
        g.push(remote_name, deployment_branch_name, force=True)

    g.checkout(source_branch_name)
    return deployment_branch_name


def checkout_to_release_branch(remote_name=None):
    repo = git.Repo('.')
    g = repo.git
    match = re.match(DEPLOYMENT_COMMIT_PATTERN, repo.head.commit.message)
    if not match:
        raise UsageError('Invalid deployment branch commit')

    branch_name = match.group('branch_name')
    g.checkout(branch_name)
    if remote_name:
        g.pull(remote_name, branch_name)
    return branch_name


def bump_version_from_release_branch(files=['version.json']):
    repo = git.Repo('.')
    g = repo.git

    match = re.match(RELEASE_BRANCH_PATTERN, str(repo.head.reference))
    if not match:
        raise UsageError('Invalid release branch')
    bump_version(match.group('version'), files)
    return match.group('version')


def commit_version(version, files=['version.json'], remote_name=None):
    repo = git.Repo('.')
    g = repo.git

    try:
        g.add(files)
        g.commit(m=str(version))
    except GitCommandError as ex:
        raise UsageError('Version files was not changed or another git error was raised: {}'.format(ex))

    try:
        g.tag(str(version))
    except GitCommandError as ex:
        raise UsageError('Tag {} already exists or another git error was raised: {}'.format(version, ex))

    if remote_name:
        g.push(remote_name, str(repo.head.reference))
        g.push(remote_name, str(version))


def merge_release_branch(to_branch_name=None, remote_name=None):
    repo = git.Repo('.')
    g = repo.git
    source_branch_name = str(repo.head.reference)

    g.checkout(to_branch_name)
    if remote_name:
        g.pull(remote_name, to_branch_name)

    # GitPython does not support merge --no-ff or what?
    git_cmd = git.cmd.Git('.')
    no_ff_commit = 'Merge branch "{}"'.format(source_branch_name)
    git_cmd.execute(('git', 'merge', '--no-ff', '-m', no_ff_commit, str(source_branch_name)))

    if remote_name:
        g.push(remote_name, to_branch_name)

    g.checkout(source_branch_name)


def get_current_branch_name():
    repo = git.Repo('.')
    return str(repo.head.reference)


def get_commit_hash(branch_name):
    try:
        repo = git.Repo('.')
        return repo.heads[branch_name].object.hexsha
    except IndexError:
        raise UsageError('Invalid branch name: {}'.format(branch_name))


def get_current_issue_key():
    branch_name = get_current_branch_name()
    match = re.match('(?P<issue_key>.{3}-\d+).*', branch_name)
    if match:
        return match.group('issue_key')
    else:
        return None
