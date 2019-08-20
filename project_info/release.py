import json
import os
import git
import re
import sys

from click import BadParameter


RELEASE_TYPES = ('major', 'minor', 'patch', 'build')

VERSION_PATTERN = r'(?P<major>[0-9]+)\.(?P<minor>[0-9]+)(\.(?P<patch>[0-9]+))?(-(?P<build>\w+))?'

VERSION_RE = re.compile(r'^{}$'.format(VERSION_PATTERN))

VERSION_FILE_RE = re.compile(r'"version": "{}"'.format(VERSION_PATTERN))


class InvalidVersion(Exception):
    pass


class Version:

    def __init__(self, version_str):
        self._parse(version_str)

    def _parse(self, version_str):
        match = VERSION_RE.match(version_str)
        if not match:
            raise InvalidVersion

        self.major = int(match.group('major'))
        self.minor = int(match.group('minor'))
        self.patch = int(match.group('patch')) if match.group('patch') else 0
        self.build = match.group('build')

    def __repr__(self):
        return (
            '{}.{}.{}-{}'.format(self.major, self.minor, self.patch, self.build) if self.build
            else '{}.{}.{}'.format(self.major, self.minor, self.patch)
        )

    def __str__(self):
        return self.__repr__()

    def replace(self, **kwargs):
        assert set(kwargs.keys()) <= {'major', 'minor', 'patch', 'build'}

        for k, v in kwargs.items():
            setattr(self, k, v)
        return self


def make_collection(string_or_tuple):
    return (string_or_tuple,) if isinstance(string_or_tuple, str) else string_or_tuple


def _write_version(project_dir, file, substitution, str_version):
    full_file_path = os.path.join(project_dir, file)
    if not os.path.isfile(full_file_path):
        raise BadParameter('File {} was not found'.format(full_file_path))

    with open(file, 'r+') as f:
        replaced = VERSION_FILE_RE.sub(substitution, f.read())
        f.seek(0)
        f.write(replaced)


def _get_project_dir(project_dir):
    return os.getcwd() if project_dir is None else project_dir


def get_version(file='version.json', project_dir=None):
    full_file_path = os.path.join(_get_project_dir(project_dir), file)
    if not os.path.isfile(full_file_path):
        raise BadParameter('File {} was not found'.format(full_file_path))

    with open(_get_project_dir(full_file_path)) as f:
        return Version(json.load(f)['version'])


def get_next_version(release_type='patch', build_hash=None, file='version.json', project_dir=None):
    if release_type not in RELEASE_TYPES:
        raise BadParameter(
            'An invalid release type given: {} \nExpected: {}'.format(release_type, ', '.join(RELEASE_TYPES))
        )

    version = get_version(file, project_dir)
    if release_type == 'build':
        if not build_hash:
            raise BadParameter('Build hash i required for realease type build')
        return version.replace(build=build_hash[:5])
    elif release_type == 'patch':
        return version.replace(build=None, patch=version.patch + 1)
    elif release_type == 'minor':
        return version.replace(build=None, patch=0, minor=version.minor + 1)
    else:
        return version.replace(build=None, patch=0, minor=0, major=version.major + 1)


def bump_version(version, files=['version.json'], project_dir=None):
    if len('files') == 0:
        raise BadParameter('Given no files to release a version')

    str_version = str(version)
    substitution = '"version": "{}"'.format(str_version)
    for file in files:
        _write_version(_get_project_dir(project_dir), file, substitution, str_version)

    return 'Bumped version to {}'.format(version)


def bump_to_next_version(release_type='patch', build_hash=None, files=['version.json'], project_dir=None):
    if len('files') == 0:
        raise BadParameter('Given no files to release a version')

    next_version = get_next_version(release_type, build_hash, files[0], project_dir)
    return bump_version(next_version, files, project_dir)


def merge_branch(git_cmd, g, branch, no_ff_commit, release_branch, origin):
    g.checkout(branch)
    git_cmd.execute(('git', 'merge', '--no-ff', '-m', no_ff_commit, release_branch))
    g.push(origin, branch)
    return ('{} to {}'.format(no_ff_commit, branch), 'Pushed {} to origin'.format(branch))


def compact(seq):
    return tuple(item for item in seq if item is not None)


def release(release_type='patch', build_hash=None, files=['version.json'], next_branch='next', origin='origin',
            project_dir=None):
    if release_type not in RELEASE_TYPES:
        raise BadParameter(
            'An invalid release type given: {} \nExpected: {}'.format(release_type, ', '.join(RELEASE_TYPES))
        )

    if len('files') == 0:
        raise BadParameter('Given no files to release a version')

    # GitPython does not support merge --no-ff or what?
    git_cmd = git.cmd.Git(project_dir)

    repo = git.Repo(project_dir)
    g = repo.git

    g.checkout(next_branch)

    g.pull(origin, next_branch)

    str_version = str(bump_to_next_version(release_type, build_hash, files, project_dir))

    release_branch = "release-" + str_version
    g.checkout(next_branch, b=release_branch)

    g.add(files)
    g.commit(m=str_version)
    print('Committed as "{}"'.format(str_version))
    g.tag(str_version)
    print('Tagged as "{}"'.format(str_version))

    g.push(origin, release_branch)

    no_ff_commit = "Merge branch 'release-{}'".format(str_version)
    for msg in (merge_branch(git_cmd, g, branch, no_ff_commit, release_branch, origin)
                for branch in ('master', next_branch)):
        info(msg)

    git_cmd.execute(('git', 'push', origin, '--tags'))

    return 0
