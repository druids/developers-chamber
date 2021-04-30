import os

import click

from developers_chamber.git_utils import get_current_branch_name
from developers_chamber.gitlab_utils import \
    create_merge_request as create_merge_request_func
from developers_chamber.scripts import cli

DEFAULT_API_URL = os.environ.get('GITLAB_API_URL', 'https://gitlab.com/api/v4')
DEFAULT_PROJECT = os.environ.get('GITLAB_PROJECT')
DEFAULT_TARGET_BRANCH = os.environ.get('GITLAB_TARGET_BRANCH', 'next')
DEFAULT_TOKEN = os.environ.get('GITLAB_TOKEN')


@cli.group()
def gitlab():
    """GitLab commands"""


@gitlab.command()
@click.option('--api-url', help='GitLab instance API URL (defaults to gitlab.com)', type=str, required=True,
              default=DEFAULT_API_URL)
@click.option('--token', help='token (can be set as env variable GITLAB_TOKEN)', type=str, required=True,
              default=DEFAULT_TOKEN)
@click.option('--source-branch', help='source Git branch', type=str)
@click.option('--target-branch', help='target Git branch (defaults to env variable GITLAB_TARGET_BRANCH)', type=str,
              default=DEFAULT_TARGET_BRANCH)
@click.option('--project', help='GitLab project name (defaults to env variable GITLAB_PROJECT)', type=str,
              required=True, default=DEFAULT_PROJECT)
def create_release_merge_request(api_url, token, source_branch, target_branch, project):
    """Create a new merge request in GitLab project after release"""
    if not source_branch:
        source_branch = get_current_branch_name()

    mr_url = create_merge_request_func(
        api_url=api_url,
        token=token,
        title=f'Merge branch "{source_branch}"',
        description='',
        source_branch=source_branch,
        target_branch=target_branch,
        project=project,
    )

    click.echo(f'Merge request was successfully created: {mr_url}')
