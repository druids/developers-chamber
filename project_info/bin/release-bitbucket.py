#!/usr/bin/env python
import click

from project_info.git_utils import get_current_branch_name
from project_info.bitbucket_utils import create_merge_release_pull_request as create_merge_release_pull_request_func


@click.group()
def cli():
    pass


@cli.command()
@click.option('--username', help='username', type=str, required=True)
@click.option('--password', help='password', type=str, required=True)
@click.option('--source_branch_name', help='source git branch name', type=str)
@click.option('--destination_branch_name', help='destination git branch name', type=str, required=True, default='next')
@click.option('--repository_name', help='git repository name', type=str, required=True)
def create_merge_release_pull_request(username, password, source_branch_name, destination_branch_name, repository_name):
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


if __name__ == '__main__':
    cli()
