#!/usr/bin/env python
import click

from project_info.git_utils import create_release_branch as create_release_branch_func
from project_info.git_utils import create_deployment_branch as create_deployment_branch_func
from project_info.git_utils import checkout_to_release_branch as checkout_to_release_branch_func
from project_info.git_utils import commit_version as commit_version_func
from project_info.git_utils import merge_release_branch as merge_release_branch_func
from project_info.version_utils import get_next_version, get_version
from project_info.types import EnumType, ReleaseType


@click.group()
def cli():
    pass


@cli.command()
@click.option('--release_type', help='release type', type=EnumType(ReleaseType), required=True)
@click.option('--file',  help='path to the version file', type=str, default='version.json', required=True)
@click.option('--remote_name', help='remote repository name if you want to push the new branch', type=str)
@click.option('--branch_name', help='branch name if you want to create branch from another repository', type=str)
def create_release_branch(release_type, file, remote_name, branch_name):
    """
    Create release branch and push it to the remote repository if remote name is specified
    """
    if release_type == ReleaseType.build:
        raise click.BadParameter('build is not allowed for release')
    click.echo(
        'New release branch "{}" was created'.format(
            create_release_branch_func(
                get_next_version(release_type, None, file), release_type, remote_name, branch_name
            )
        )
    )


@cli.command()
@click.option('--environment', help='deployment environment', type=str, required=True)
def create_deployment_branch(environment):
    """
    Create deployment branch and new commit to trigger a deployment event
    """
    click.echo(
        'New deployment branch "{}" was created'.format(
            create_deployment_branch_func(environment)
        )
    )


@cli.command()
def checkout_to_release_branch():
    """
    Checkout git repository back to the release branch from deployment branch
    """
    click.echo(
        'Git is on "{}" branch now'.format(
            checkout_to_release_branch_func()
        )
    )


@cli.command()
@click.option('--file',  help='path to the version file', type=str, default=['version.json'], required=True,
              multiple=True)
@click.option('--remote_name', help='remote repository name if you want to push the new branch', type=str)
def commit_version(file, remote_name):
    """
    Commit version files and add git tag to the commit
    """
    commit_version_func(get_version(file[0]), file, remote_name)
    click.echo('Version commit change was successfully created')


@cli.command()
@click.option('--to_branch_name', help='branch name', type=str, required=True)
@click.option('--remote_name', help='remote repository name if you want to push the new branch', type=str)
def merge_release_branch(to_branch_name, remote_name):
    """
    Merge current branch to the selected branch
    """
    merge_release_branch_func(to_branch_name, remote_name)
    click.echo('Branch was successfully merged')


if __name__ == '__main__':
    cli()
