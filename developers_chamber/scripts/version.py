import os

import click

from developers_chamber.scripts import cli
from developers_chamber.types import EnumType, ReleaseType
from developers_chamber.version_utils import \
    bump_to_next_version as bump_to_next_version_func
from developers_chamber.version_utils import get_next_version, get_version


default_version_files = os.environ.get('VERSION_FILES', 'version.json').split(',')


@cli.group()
def version():
    """Helpers for automatic update version in the version file."""


@version.command()
@click.option('--release-type', '-r', help='release type', type=EnumType(ReleaseType), required=True)
@click.option('--build-hash', '-h',  help='hash of the build', type=str)
@click.option('--file', '-f',  help='path to the version file', type=str, default=default_version_files, required=True,
              multiple=True)
def bump_to_next(release_type, build_hash, file):
    """
    Bump version in the JSON file (or files) and print it.
    Version is selected according to release type, build has and version file.

    \b
    * version file - contains current version in json format,
                     example (version is "1.30.0"): {"version": "1.30.0"}
    * release type - select one of the values
        * build - first 5 characters from build hash is joined to the end of
                  the current version
                  example: "1.30.0-abcde" will be generated for a version 1.30.0
                           and a build hash "abcdefghi"
        * patch - current version is "1.30.0", next version will be "1.30.1"
        * minor - current version is "1.30.1", next version will be "1.31.0"
        * major - current version is "1.30.2", next version will be "2.0.0"
    * build-hash - only required for release type "build"
    """
    click.echo(bump_to_next_version_func(release_type, build_hash, file))


@version.command(name='print')
@click.option('--file', '-f', help='path to the version file', type=str, default=default_version_files[0],
              required=True)
def print_version(file):
    """
    Return current project version according to version JSON file
    \b
    * version file - contains current version in json format,
                     example (version is "1.30.0"): {"version": "1.30.0"}
    """
    click.echo(get_version(file))


@version.command()
@click.option('--release-type', '-r', help='release type', type=EnumType(ReleaseType), required=True)
@click.option('--build-hash', '-h',  help='hash of the build', type=str)
@click.option('--file', '-f',  help='path to the version file', type=str, default=default_version_files[0],
              required=True)
def print_next(release_type, build_hash, file):
    """
    Return next version according to input release type, build hash and version JSON file

    \b
    * version file - contains current version in json format,
                     example (version is "1.30.0"): {"version": "1.30.0"}
    * release type - select one of the values
        * build - first 5 characters from build hash is joined to the end of
                  the current version
                  example: "1.30.0-abcde" will be generated for a version 1.30.0
                           and a build hash "abcdefghi"
        * patch - current version is "1.30.0", next version will be "1.30.1"
        * minor - current version is "1.30.1", next version will be "1.31.0"
        * major - current version is "1.30.2", next version will be "2.0.0"
    * build-hash - only required for release type "build"
    """
    click.echo(get_next_version(release_type, build_hash, file))
