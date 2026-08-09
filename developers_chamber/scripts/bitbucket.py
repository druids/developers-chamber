
import click

from developers_chamber.bitbucket_utils import (
    create_merge_release_pull_request as create_merge_release_pull_request_func,
)
from developers_chamber.git_utils import get_current_branch_name
from developers_chamber.scripts import cli




@cli.group()
def bitbucket():
    """Bitbucket management commands"""


@bitbucket.command()
@click.option(
    "--username",
    "-u",
    help="username",
    type=str,
    required=True,
    envvar="BITBUCKET_USERNAME",
)
@click.option(
    "--password",
    "-p",
    help="password",
    type=str,
    required=True,
    envvar="BITBUCKET_PASSWORD",
)
@click.option("--source-branch-name", "-s", help="source git branch name", type=str)
@click.option(
    "--destination-branch-name",
    "-d",
    help="destination git branch name",
    type=str,
    required=True,
    envvar="BITBUCKET_BRANCH_NAME",
    default="next",
)
@click.option(
    "--repository-name",
    "-r",
    help="git repository name",
    type=str,
    required=True,
    envvar="BITBUCKET_REPOSITORY",
)
def create_release_pull_request(
    username, password, source_branch_name, destination_branch_name, repository_name
):
    """
    Create a new pull request to the bitbucket repository.
    """
    if not source_branch_name:
        source_branch_name = get_current_branch_name()

    click.echo(
        "Pull request was successfully created, url: {}".format(
            create_merge_release_pull_request_func(
                username,
                password,
                source_branch_name,
                destination_branch_name,
                repository_name,
            )
        )
    )
