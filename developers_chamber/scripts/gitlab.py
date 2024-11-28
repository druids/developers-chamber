import os

import click

from developers_chamber.gitlab_utils import (
    create_merge_request as create_merge_request_func,
    activate_automerge as activate_automerge_func,
    run_job as run_job_func,
)
from developers_chamber.scripts import cli

DEFAULT_API_URL = os.environ.get("GITLAB_API_URL", "https://gitlab.com/api/v4")
DEFAULT_PROJECT = os.environ.get("GITLAB_PROJECT")
DEFAULT_TARGET_BRANCH = os.environ.get("GITLAB_TARGET_BRANCH", "next")
DEFAULT_TOKEN = os.environ.get("GITLAB_TOKEN")


@cli.group()
def gitlab():
    """Helpers for GitLab management"""


@gitlab.command()
@click.option(
    "--api-url",
    help="GitLab instance API URL (defaults to gitlab.com)",
    type=str,
    required=True,
    default=DEFAULT_API_URL,
)
@click.option(
    "--token",
    help="token (can be set as env variable GITLAB_TOKEN)",
    type=str,
    required=True,
    default=DEFAULT_TOKEN,
)
@click.option("--source-branch", help="source Git branch", type=str)
@click.option(
    "--target-branch",
    help="target Git branch (defaults to env variable GITLAB_TARGET_BRANCH)",
    type=str,
    default=DEFAULT_TARGET_BRANCH,
)
@click.option(
    "--project",
    help="GitLab project name (defaults to env variable GITLAB_PROJECT)",
    type=str,
    required=True,
    default=DEFAULT_PROJECT,
)
@click.option(
    "--assignee-id",
    help="User ID to assign the merge request",
    type=str,
    required=False,
    default=DEFAULT_PROJECT,
)
def create_release_merge_request(api_url, token, source_branch, target_branch, project, assignee_id=None):
    """
    Create a new merge request in a GitLab project. It is often used after the project release.
    """
    if not source_branch:
        from developers_chamber.git_utils import get_current_branch_name

        source_branch = get_current_branch_name()

    mr_url = create_merge_request_func(
        api_url=api_url,
        token=token,
        title=f'Merge branch "{source_branch}"',
        description="",
        source_branch=source_branch,
        target_branch=target_branch,
        project=project,
        assignee_id=assignee_id
    )

    click.echo(f"Merge request was successfully created: {mr_url}")


@gitlab.command()
@click.option(
    "--api-url",
    help="GitLab instance API URL (defaults to gitlab.com)",
    type=str,
    required=True,
    default=DEFAULT_API_URL,
)
@click.option(
    "--token",
    help="token (can be set as env variable GITLAB_TOKEN)",
    type=str,
    required=True,
    default=DEFAULT_TOKEN,
)
@click.option("--source-branch", help="source Git branch", type=str)
@click.option(
    "--target-branch",
    help="Target Git branch (defaults to env variable GITLAB_TARGET_BRANCH)",
    type=str,
    default=DEFAULT_TARGET_BRANCH,
)
@click.option(
    "--title",
    help="Merge request title",
    type=str,
    default=DEFAULT_TARGET_BRANCH,
)
@click.option(
    "--project",
    help="GitLab project name (defaults to env variable GITLAB_PROJECT)",
    type=str,
    required=True,
    default=DEFAULT_PROJECT,
)
@click.option(
    "--automerge",
    help="User ID to assign the merge request",
    is_flag=True,
    default=False,
)
@click.option(
    "--assignee-id",
    help="User ID to assign the merge request",
    type=str,
    required=False,
    default=DEFAULT_PROJECT,
)
def create_merge_request(api_url, token, source_branch, target_branch, title, project, automerge, assignee_id=None):
    """
    Create a new merge request in a GitLab project. It is often used after the project release.
    """
    mr_url = create_merge_request_func(
        api_url=api_url,
        token=token,
        title=title,
        description="",
        source_branch=source_branch,
        target_branch=target_branch,
        project=project,
        assignee_id=assignee_id,
        automerge=automerge
    )

    click.echo(f"Merge request was successfully created: {mr_url}")

@gitlab.command()
@click.option(
    "--api-url",
    help="GitLab instance API URL (defaults to gitlab.com)",
    type=str,
    required=True,
    default=DEFAULT_API_URL,
)
@click.option(
    "--token",
    help="token (can be set as env variable GITLAB_TOKEN)",
    type=str,
    required=True,
    default=DEFAULT_TOKEN,
)
@click.option(
    "--project",
    help="GitLab project name (defaults to env variable GITLAB_PROJECT)",
    type=str,
    required=True,
    default=DEFAULT_PROJECT,
)
@click.option(
    "--merge-request-id",
    help="GitLab merge request ID",
    type=str,
    required=True,
)
def activate_merge_request_automerge(api_url, token, project, merge_request_id):
    """
    Create a new merge request in a GitLab project. It is often used after the project release.
    """
    message = activate_automerge_func(
        api_url=api_url,
        token=token,
        project=project,
        merge_request_id=merge_request_id
    )

    click.echo(f"{message}")


@gitlab.command()
@click.option(
    "--api-url",
    help="GitLab instance API URL (defaults to gitlab.com)",
    type=str,
    required=True,
    default=DEFAULT_API_URL,
)
@click.option(
    "--token",
    help="token (can be set as env variable GITLAB_TOKEN)",
    type=str,
    required=True,
    default=DEFAULT_TOKEN,
)
@click.option(
    "--project",
    help="GitLab project name (defaults to env variable GITLAB_PROJECT)",
    type=str,
    required=True,
    default=DEFAULT_PROJECT,
)
@click.option(
    "--branch",
    help="Branch name",
    type=str,
    required=True,
)
@click.option(
    "--variables",
    help="Variables",
    type=str,
    required=False,
)
def run_job(api_url, token, project, branch, variables):
    """
    Run a job in a GitLab project.
    """
    variables = dict([var.split('=') for var in variables.split(',')]) if variables else {}
    ci_job_url = run_job_func(api_url, token, project, f'refs/heads/{branch}', variables)

    click.echo(f"CI job was started: {ci_job_url}")