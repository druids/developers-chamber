import os

import click

from developers_chamber.scripts import cli
from developers_chamber.git import get_current_branch_name
from developers_chamber.bitbucket import create_merge_release_pull_request as \
    create_merge_release_pull_request_func


default_username = os.environ.get('BITBUCKET_USERNAME')
default_password = os.environ.get('BITBUCKET_PASSWORD')
default_destination_branch_name = os.environ.get('BITBUCKET_BRANCH_NAME', 'next')
default_repository_name = os.environ.get('BITBUCKET_REPOSITORY')


@cli.command()
@click.option('--username', help='username', type=str, required=True, default=default_username)
@click.option('--password', help='password', type=str, required=True,
              default=default_password)
@click.option('--source_branch_name', help='source git branch name', type=str)
@click.option('--destination_branch_name', help='destination git branch name', type=str, required=True,
              default=default_destination_branch_name)
@click.option('--repository_name', help='git repository name', type=str, required=True, default=default_repository_name)
def bitbucket_create_release_pull_request(username, password, source_branch_name, destination_branch_name,
                                          repository_name):
    """
    Create new pull request to the bitbucket repository
    """
    if not source_branch_name:
        source_branch_name = get_current_branch_name()

    click.echo(
        'Pull request was successfully created, url: {}'.format(
            create_merge_release_pull_request_func(
                username, password, source_branch_name, destination_branch_name, repository_name
            )
        )
    )
