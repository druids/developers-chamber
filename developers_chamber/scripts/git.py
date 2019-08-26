import os

import click

from developers_chamber.scripts import cli
from developers_chamber.git_utils import create_release_branch as create_release_branch_func
from developers_chamber.git_utils import create_deployment_branch as create_deployment_branch_func
from developers_chamber.git_utils import checkout_to_release_branch as checkout_to_release_branch_func
from developers_chamber.git_utils import commit_version as commit_version_func
from developers_chamber.git_utils import merge_release_branch as merge_release_branch_func
from developers_chamber.git_utils import bump_version_from_release_branch as bump_version_from_release_branch_func
from developers_chamber.version_utils import get_next_version, get_version
from developers_chamber.types import EnumType, ReleaseType

from .version import default_version_files


default_remote_name = os.environ.get('GIT_REMOTE_NAME')
default_branch_name = os.environ.get('GIT_BRANCH_NAME')


@cli.command()
@click.option('--release_type', help='release type', type=EnumType(ReleaseType), required=True)
@click.option('--file',  help='path to the version file', type=str, default=default_version_files[0], required=True)
@click.option('--remote_name', help='remote repository name if you want to push the new branch', type=str,
              default=default_remote_name)
@click.option('--branch_name', help='branch name if you want to create branch from another repository', type=str,
              default=default_branch_name)
def git_create_release_branch(release_type, file, remote_name, branch_name):
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
@click.option('--remote_name', help='remote repository name if you want to push the new branch', type=str,
              default=default_remote_name)
def git_create_deployment_branch(environment, remote_name):
    """
    Create deployment branch and new commit to trigger a deployment event
    """
    click.echo(
        'New deployment branch "{}" was created'.format(
            create_deployment_branch_func(environment, remote_name)
        )
    )


@cli.command()
def git_checkout_to_release_branch():
    """
    Checkout git repository back to the release branch from deployment branch
    """
    click.echo(
        'Git is on "{}" branch now'.format(
            checkout_to_release_branch_func()
        )
    )


@cli.command()
@click.option('--file',  help='path to the version file', type=str, default=default_version_files, required=True,
              multiple=True)
def git_bump_version_from_release_branch(file):
    """
    Get version from release branch and bump version files
    """
    click.echo(
        'Version bumped to "{}"'.format(
            bump_version_from_release_branch_func(file)
        )
    )


@cli.command()
@click.option('--file',  help='path to the version file', type=str, default=default_version_files, required=True,
              multiple=True)
@click.option('--remote_name', help='remote repository name if you want to push the new branch', type=str,
              default=default_remote_name)
def git_commit_version(file, remote_name):
    """
    Commit version files and add git tag to the commit
    """
    commit_version_func(get_version(file[0]), file, remote_name)
    click.echo('Version commit change was successfully created')


@cli.command()
@click.option('--to_branch_name', help='branch name', type=str, required=True)
@click.option('--remote_name', help='remote repository name if you want to push the new branch', type=str,
              default=default_remote_name)
def git_merge_release_branch(to_branch_name, remote_name):
    """
    Merge current branch to the selected branch
    """
    merge_release_branch_func(to_branch_name, remote_name)
    click.echo('Branch was successfully merged')
