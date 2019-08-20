#!/usr/bin/env python
import sys
import argparse

import click

from project_info.release import release as release_func
from project_info.release import bump_to_next_version as bump_to_next_version_func
from project_info.release import get_next_version, get_version, RELEASE_TYPES


@click.group()
def cli():
    pass


@cli.command()
@click.option('--release_type', help='release type', type=click.Choice(RELEASE_TYPES))
@click.option('--build_hash',  help='hash of the build', type=str)
@click.option('--files',  help='path to the version files', type=list, default=['version.json'])
@click.option('--branch_name', help='branch name', type=str, default='next')
@click.option('--repository_name', help='repository name', type=str, default='origin')
@click.option('--project_directory', help='project directory', type=str)
def release(release_type, build_hash, files, branch_name, repository_name, project_directory):
    release_func(release_type, build_hash, files, branch_name, repository_name, project_directory)


@cli.command()
@click.option('--release_type', help='release type', type=click.Choice(RELEASE_TYPES))
@click.option('--build_hash',  help='hash of the build', type=str)
@click.option('--files',  help='path to the version files', type=list, default=['version.json'])
@click.option('--project_directory', help='project directory', type=str)
def bump_to_next_version(release_type, build_hash, files, project_directory):
    click.echo(bump_to_next_version_func(release_type, build_hash, files, project_directory))


@cli.command()
@click.option('--file',  help='path to the version file', type=str, default='version.json')
@click.option('--project_directory', help='project directory', type=str)
def version(file, project_directory):
    click.echo(get_version(file, project_directory))


@cli.command()
@click.option('--release_type', help='release type', type=click.Choice(RELEASE_TYPES))
@click.option('--build_hash',  help='hash of the build', type=str)
@click.option('--file',  help='path to the version file', type=str, default='version.json')
@click.option('--project_directory', help='project directory', type=str)
def next_version(release_type, build_hash, file, project_directory):
    click.echo(get_next_version(release_type, build_hash, file, project_directory))


if __name__ == '__main__':
    cli()
