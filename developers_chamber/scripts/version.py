import os

import click

from developers_chamber.scripts import cli
from developers_chamber.version_utils import bump_to_next_version as bump_to_next_version_func
from developers_chamber.version_utils import get_next_version, get_version
from developers_chamber.types import EnumType, ReleaseType


default_version_files = os.environ.get('VERSION_FILES', 'version.json').split(',')


@cli.group()
def version():
    """Version file commands"""


@version.command()
@click.option('--release-type', '-r', help='release type', type=EnumType(ReleaseType), required=True)
@click.option('--build-hash', '-h',  help='hash of the build', type=str)
@click.option('--file', '-f',  help='path to the version file', type=str, default=default_version_files, required=True,
              multiple=True)
def bump_to_next(release_type, build_hash, file):
    """
    Bump JSON file (or files) version number
    """
    click.echo(bump_to_next_version_func(release_type, build_hash, file))


@version.command(name='print')
@click.option('--file', '-f', help='path to the version file', type=str, default=default_version_files[0],
              required=True)
def print_version(file):
    """
    Return current project version according to version JSON file
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
    """
    click.echo(get_next_version(release_type, build_hash, file))
