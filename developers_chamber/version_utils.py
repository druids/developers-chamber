import json
import os
import re

import xml.etree.ElementTree as ET
import toml
from click import BadParameter

from .types import ReleaseType, VersionFileType

VERSION_PATTERN = (
    r"(?P<major>[0-9]+)\.(?P<minor>[0-9]+)(\.(?P<patch>[0-9]+))?(-(?P<build>\w+))?"
)


class InvalidVersion(Exception):
    pass


class Version:
    VERSION_RE = re.compile(r"^{}$".format(VERSION_PATTERN))

    def __init__(self, version_str):
        self._parse(version_str)

    def _parse(self, version_str):
        match = self.VERSION_RE.match(version_str)
        if not match:
            raise InvalidVersion

        self.major = int(match.group("major"))
        self.minor = int(match.group("minor"))
        self.patch = int(match.group("patch")) if match.group("patch") else 0
        self.build = match.group("build")

    def __repr__(self):
        return (
            "{}.{}.{}-{}".format(self.major, self.minor, self.patch, self.build)
            if self.build
            else "{}.{}.{}".format(self.major, self.minor, self.patch)
        )

    def __str__(self):
        return self.__repr__()

    def replace(self, **kwargs):
        assert set(kwargs.keys()) <= {"major", "minor", "patch", "build"}

        for k, v in kwargs.items():
            setattr(self, k, v)
        return self


class TomlNewlineArraySeparatorEncoder(toml.TomlEncoder):

    def dump_list(self, v):
        t = []
        retval = "[\n"

        for u in v:
            retval += "    " + str(self.dump_value(u)) + ",\n"
        retval += "]"
        return retval


def _write_version_to_file(file, new_version, file_type=None):
    """Rewrite version number in the file"""
    full_file_path = os.path.join(os.getcwd(), file)
    filename, file_extension = os.path.splitext(full_file_path)
    if not os.path.isfile(full_file_path):
        raise BadParameter("File {} was not found".format(full_file_path))

    file_type = file_type or file_extension[1:]

    with open(full_file_path, "r+") as f:
        if file_type == VersionFileType.toml:
            data = toml.load(f)
            data["project"]["version"] = new_version
            f.seek(0)
            f.truncate()
            toml.dump(data, f, encoder=TomlNewlineArraySeparatorEncoder())
        elif file_type == VersionFileType.json:
            data = json.load(f)
            data["version"] = str(new_version)
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2)
        elif file_type == VersionFileType.npm:
            lock_file = f"{file.rsplit('.', 1)[0]}-lock.{file.rsplit('.', 1)[1]}"
            full_lock_file_path = os.path.join(os.getcwd(), lock_file)
            if not os.path.isfile(full_lock_file_path):
                raise BadParameter(f"Lock file {full_lock_file_path} was not found")
            with open(full_lock_file_path, "r+") as lf:
                file_data = json.load(f)
                file_data["version"] = str(new_version)
                lock_file_data = json.load(lf)
                lock_file_data["version"] = str(new_version)
                lock_file_data["packages"][""]["version"] = str(new_version)
                f.seek(0)
                f.truncate()
                lf.seek(0)
                lf.truncate()
                json.dump(file_data, f, indent=2)
                json.dump(lock_file_data, lf, indent=2)
        elif file_type == VersionFileType.xml:
            ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
            tree = ET.parse(f)
            root = tree.getroot()
            version = root.find("{http://maven.apache.org/POM/4.0.0}version")
            version.text = str(new_version)
            tree.write(full_file_path, xml_declaration=True, encoding="utf-8", method="xml")
        else:
            raise BadParameter(f'Invalid version type "{file_type}"')


def get_version_files(file, file_type=None):
    version_files = [file]
    if file_type == VersionFileType.npm:
        lock_file = f"{file.rsplit('.', 1)[0]}-lock.{file.rsplit('.', 1)[1]}"
        full_lock_file_path = os.path.join(os.getcwd(), lock_file)
        if os.path.isfile(full_lock_file_path):
            version_files.append(lock_file)
    return version_files


def get_version(file="version.json"):
    full_file_path = os.path.join(os.getcwd(), file)
    filename, file_extension = os.path.splitext(full_file_path)
    try:
        with open(full_file_path) as f:
            if file_extension == ".toml":
                return Version(toml.load(f)["project"]["version"])
            elif file_extension == ".json":
                return Version(json.load(f)["version"])
            elif file_extension == ".xml":
                return Version(read_version_from_pom())
            else:
                raise BadParameter(f'Invalid file format "{full_file_path}"')
    except FileNotFoundError:
        raise BadParameter("File {} was not found".format(full_file_path))


def get_next_version(release_type, build_hash=None, file="version.json"):
    """Return next version according to previous version, release type and build hash"""

    version = get_version(file)
    if release_type == ReleaseType.build:
        if not build_hash:
            raise BadParameter("Build hash is required for realease type build")
        return version.replace(build=build_hash[:5])
    elif release_type == ReleaseType.patch:
        return version.replace(build=None, patch=version.patch + 1)
    elif release_type == ReleaseType.minor:
        return version.replace(build=None, patch=0, minor=version.minor + 1)
    else:
        return version.replace(build=None, patch=0, minor=0, major=version.major + 1)


def bump_version(version, files=["version.json"], file_type=None):
    """Bump version in the input files"""

    if len("files") == 0:
        raise BadParameter("Given no files to release a version")

    for file in files:
        _write_version_to_file(file, version, file_type)

    return "Bumped version to {}".format(version)


def bump_to_next_version(
        release_type, build_hash=None, files=["version.json"], file_type=None
):
    """Bump version to the next version according to previous version, release type and build hash"""

    if len("files") == 0:
        raise BadParameter("Given no files to release a version")

    next_version = get_next_version(release_type, build_hash, files[0])
    return bump_version(next_version, files, file_type)


def read_version_from_pom(file="pom.xml"):
    full_file_path = os.path.join(os.getcwd(), file)
    if not os.path.isfile(full_file_path):
        raise BadParameter("File {} was not found".format(full_file_path))

    try:
        tree = ET.parse(full_file_path)
        root = tree.getroot()
        version = root.find("{http://maven.apache.org/POM/4.0.0}version")
        return version.text
    except KeyError:
        raise BadParameter("Could not find revision in pom.xml")
