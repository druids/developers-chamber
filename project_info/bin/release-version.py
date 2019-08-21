#!/usr/bin/env python
import click

from project_info.version_utils import bump_to_next_version as bump_to_next_version_func
from project_info.version_utils import get_next_version, get_version
from project_info.types import EnumType, ReleaseType


@click.group()
def cli():
    pass


@cli.command()
@click.option('--release_type', help='release type', type=EnumType(ReleaseType), required=True)
@click.option('--build_hash',  help='hash of the build', type=str)
@click.option('--file',  help='path to the version file', type=str, default=['version.json'], required=True,
              multiple=True)
def bump_to_next_version(release_type, build_hash, file):
    """
    Bump JSON file (or files) version number
    """
    click.echo(bump_to_next_version_func(release_type, build_hash, file))


@cli.command()
@click.option('--file', help='path to the version file', type=str, default='version.json', required=True)
def version(file):
    """
    Return current project version according to version JSON file
    """
    click.echo(get_version(file))


@cli.command()
@click.option('--release_type', help='release type', type=EnumType(ReleaseType), required=True)
@click.option('--build_hash',  help='hash of the build', type=str)
@click.option('--file',  help='path to the version file', type=str, default='version.json', required=True)
def next_version(release_type, build_hash, file):
    """
    Return next version according to input release type, build hash and version JSON file
    """
    click.echo(get_next_version(release_type, build_hash, file))


if __name__ == '__main__':
    cli()
