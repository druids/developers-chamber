import json
import os
import re

import xml.etree.ElementTree as ET
import toml
from click import BadParameter

from .types import PreReleaseType, ReleaseType, VersionFileType

VERSION_PATTERN = (
    r"(?P<major>[0-9]+)\.(?P<minor>[0-9]+)(\.(?P<patch>[0-9]+))?"
    r"(-(?:(?P<pre_release>alpha|beta|rc)\.(?P<pre_release_num>[0-9]+)|(?P<build>[a-zA-Z0-9]+)))?"
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
        self.pre_release = match.group("pre_release")
        self.pre_release_num = (
            int(match.group("pre_release_num"))
            if match.group("pre_release_num")
            else None
        )
        self.build = match.group("build") if not self.pre_release else None

    def __repr__(self):
        base = "{}.{}.{}".format(self.major, self.minor, self.patch)
        if self.pre_release:
            return "{}-{}.{}".format(base, self.pre_release, self.pre_release_num)
        if self.build:
            return "{}-{}".format(base, self.build)
        return base

    def __str__(self):
        return self.__repr__()

    def replace(self, **kwargs):
        assert set(kwargs.keys()) <= {
            "major",
            "minor",
            "patch",
            "build",
            "pre_release",
            "pre_release_num",
        }

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


def _resolve_file_type(file_type, file_extension):
    """Prefer the explicit file type, otherwise detect it from the extension.

    Files without an extension (e.g. a Ruby-style plain text VERSION file) hold
    only the bare version number, so they default to the text type.
    """
    return file_type or file_extension[1:] or VersionFileType.text


def _write_version_to_file(file, new_version, file_type=None):
    """Rewrite version number in the file"""
    full_file_path = os.path.join(os.getcwd(), file)
    filename, file_extension = os.path.splitext(full_file_path)
    if not os.path.isfile(full_file_path):
        raise BadParameter("File {} was not found".format(full_file_path))

    file_type = _resolve_file_type(file_type, file_extension)

    with open(full_file_path, "r+", encoding="utf-8") as f:
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
            json.dump(data, f, indent=2, ensure_ascii=False)
        elif file_type == VersionFileType.npm:
            lock_file = f"{file.rsplit('.', 1)[0]}-lock.{file.rsplit('.', 1)[1]}"
            full_lock_file_path = os.path.join(os.getcwd(), lock_file)
            if not os.path.isfile(full_lock_file_path):
                raise BadParameter(f"Lock file {full_lock_file_path} was not found")
            with open(full_lock_file_path, "r+", encoding="utf-8") as lf:
                file_data = json.load(f)
                file_data["version"] = str(new_version)
                lock_file_data = json.load(lf)
                lock_file_data["version"] = str(new_version)
                lock_file_data["packages"][""]["version"] = str(new_version)
                f.seek(0)
                f.truncate()
                lf.seek(0)
                lf.truncate()
                json.dump(file_data, f, indent=2, ensure_ascii=False)
                json.dump(lock_file_data, lf, indent=2, ensure_ascii=False)
        elif file_type == VersionFileType.xml:
            ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
            tree = ET.parse(f)
            root = tree.getroot()
            version = root.find("{http://maven.apache.org/POM/4.0.0}version")
            version.text = str(new_version)
            tree.write(
                full_file_path, xml_declaration=True, encoding="utf-8", method="xml"
            )
        elif file_type == VersionFileType.text:
            f.seek(0)
            f.truncate()
            f.write(str(new_version))
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


def get_version(file="version.json", file_type=None):
    full_file_path = os.path.join(os.getcwd(), file)
    filename, file_extension = os.path.splitext(full_file_path)

    file_type = _resolve_file_type(file_type, file_extension)

    try:
        with open(full_file_path, encoding="utf-8") as f:
            if file_type == VersionFileType.toml:
                return Version(toml.load(f)["project"]["version"])
            elif file_type in (VersionFileType.json, VersionFileType.npm):
                return Version(json.load(f)["version"])
            elif file_type == VersionFileType.xml:
                return Version(read_version_from_pom())
            elif file_type == VersionFileType.text:
                return Version(f.read().strip())
            else:
                raise BadParameter(f'Invalid file format "{full_file_path}"')
    except FileNotFoundError:
        raise BadParameter("File {} was not found".format(full_file_path))


def get_next_version(
    release_type=None,
    build_hash=None,
    pre_release=None,
    file="version.json",
    file_type=None,
):
    """Return next version according to previous version, release type, pre-release stage and build hash"""

    version = get_version(file, file_type)

    if release_type == ReleaseType.build:
        if not build_hash:
            raise BadParameter("Build hash is required for release type build")
        return version.replace(
            build=build_hash[:5], pre_release=None, pre_release_num=None
        )

    if release_type == ReleaseType.release:
        return version.replace(pre_release=None, pre_release_num=None, build=None)

    if pre_release is not None:
        pre_release_str = str(pre_release)

        if release_type is None and not version.pre_release:
            raise BadParameter(
                f"Cannot add pre-release stage to a stable version without specifying --release-type "
                f"(patch, minor or major)."
            )

        if release_type == ReleaseType.patch:
            raise BadParameter(
                "Pre-release is not allowed for patch releases. Use -r patch without -p."
            )

        if (
            release_type in {ReleaseType.minor, ReleaseType.major}
            and pre_release_str != "alpha"
        ):
            raise BadParameter(
                f"When bumping the base version, pre-release stage must be 'alpha'. "
                f"Use -p alpha to start a new pre-release cycle."
            )

        if (
            release_type is None
            and version.pre_release
            and version.pre_release != pre_release_str
        ):
            order = ["alpha", "beta", "rc"]
            if order.index(pre_release_str) < order.index(version.pre_release):
                raise BadParameter(
                    f"Cannot downgrade pre-release stage from '{version.pre_release}' to '{pre_release_str}'. "
                    f"Use --release-type to bump the base version first."
                )

        if release_type == ReleaseType.patch:
            version.replace(patch=version.patch + 1)
        elif release_type == ReleaseType.minor:
            version.replace(minor=version.minor + 1, patch=0)
        elif release_type == ReleaseType.major:
            version.replace(major=version.major + 1, minor=0, patch=0)

        if version.pre_release == pre_release_str and release_type is None:
            return version.replace(
                pre_release_num=version.pre_release_num + 1, build=None
            )
        else:
            return version.replace(
                pre_release=pre_release_str, pre_release_num=1, build=None
            )

    if release_type == ReleaseType.patch:
        return version.replace(
            build=None, pre_release=None, pre_release_num=None, patch=version.patch + 1
        )
    elif release_type == ReleaseType.minor:
        return version.replace(
            build=None,
            pre_release=None,
            pre_release_num=None,
            patch=0,
            minor=version.minor + 1,
        )
    else:
        return version.replace(
            build=None,
            pre_release=None,
            pre_release_num=None,
            patch=0,
            minor=0,
            major=version.major + 1,
        )


def bump_version(version, files=["version.json"], file_type=None):
    """Bump version in the input files"""

    if len(files) == 0:
        raise BadParameter("Given no files to release a version")

    for file in files:
        _write_version_to_file(file, version, file_type)

    return "Bumped version to {}".format(version)


def bump_to_next_version(
    release_type=None,
    build_hash=None,
    pre_release=None,
    files=["version.json"],
    file_type=None,
):
    """Bump version to the next version according to previous version, release type, pre-release stage and build hash"""

    if len(files) == 0:
        raise BadParameter("Given no files to release a version")

    next_version = get_next_version(
        release_type, build_hash, pre_release, files[0], file_type
    )
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
