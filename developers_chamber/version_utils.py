import json
import os
import re

from click import BadParameter

from .types import ReleaseType

VERSION_PATTERN = r'(?P<major>[0-9]+)\.(?P<minor>[0-9]+)(\.(?P<patch>[0-9]+))?(-(?P<build>\w+))?'


class InvalidVersion(Exception):
    pass


class Version:

    VERSION_RE = re.compile(r'^{}$'.format(VERSION_PATTERN))

    def __init__(self, version_str):
        self._parse(version_str)

    def _parse(self, version_str):
        match = self.VERSION_RE.match(version_str)
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


def _write_version_to_file(file, new_version):
    """Rewrite version number in the file"""

    VERSION_FILE_RE = re.compile(r'"version": "{}"'.format(VERSION_PATTERN))

    substitution = '"version": "{}"'.format(new_version)
    full_file_path = os.path.join(os.getcwd(), file)
    if not os.path.isfile(full_file_path):
        raise BadParameter('File {} was not found'.format(full_file_path))

    with open(file, 'r+') as f:
        replaced = VERSION_FILE_RE.sub(substitution, f.read())
        f.seek(0)
        f.write(replaced)


def get_version(file='version.json'):
    full_file_path = os.path.join(os.getcwd(), file)
    try:
        with open(full_file_path) as f:
            return Version(json.load(f)['version'])
    except FileNotFoundError:
        raise BadParameter('File {} was not found'.format(full_file_path))


def get_next_version(release_type, build_hash=None, file='version.json'):
    """Return next version according to previous version, release type and build hash"""

    version = get_version(file)
    if release_type == ReleaseType.build:
        if not build_hash:
            raise BadParameter('Build hash i required for realease type build')
        return version.replace(build=build_hash[:5])
    elif release_type == ReleaseType.patch:
        return version.replace(build=None, patch=version.patch + 1)
    elif release_type == ReleaseType.minor:
        return version.replace(build=None, patch=0, minor=version.minor + 1)
    else:
        return version.replace(build=None, patch=0, minor=0, major=version.major + 1)


def bump_version(version, files=['version.json']):
    """Bump version in the input files"""

    if len('files') == 0:
        raise BadParameter('Given no files to release a version')

    for file in files:
        _write_version_to_file(file, version)

    return 'Bumped version to {}'.format(version)


def bump_to_next_version(release_type, build_hash=None, files=['version.json']):
    """Bump version to the next version according to previous version, release type and build hash"""

    if len('files') == 0:
        raise BadParameter('Given no files to release a version')

    next_version = get_next_version(release_type, build_hash, files[0])
    return bump_version(next_version, files)
