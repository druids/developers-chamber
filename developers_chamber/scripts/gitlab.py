import os

import click

from developers_chamber.gitlab_utils import (
    create_merge_request as create_merge_request_func,
    activate_automerge as activate_automerge_func,
    run_job as run_job_func,
    get_project_id as get_project_id_func,
    create_release_record as create_release_record_func,
    parse_asset_links,
)
from developers_chamber.scripts import cli
from developers_chamber.git_utils import get_remote_url, get_remote_path


def _default_gitlab_url():
    """Without its own setting the web url is the api url without the /api/v4 suffix."""
    api_url = os.environ.get("GITLAB_API_URL")
    return api_url and api_url.split("/api/v4")[0]


@cli.group()
def gitlab():
    """Helpers for GitLab management"""


@gitlab.command()
@click.option(
    "--url",
    help="GitLab instance API URL (defaults to gitlab.com)",
    type=str,
    required=False,
    envvar="GITLAB_URL",
    default=_default_gitlab_url,
)
@click.option(
    "--token",
    help="token (can be set as env variable GITLAB_TOKEN)",
    type=str,
    required=True,
    envvar="GITLAB_TOKEN",
)
@click.option("--source-branch", help="source Git branch", type=str)
@click.option(
    "--target-branch",
    help="target Git branch (defaults to env variable GITLAB_TARGET_BRANCH)",
    type=str,
    envvar="GITLAB_TARGET_BRANCH",
    default="next",
)
@click.option(
    "--project",
    help="GitLab project name (defaults to env variable GITLAB_PROJECT)",
    type=str,
    required=False,
    envvar="GITLAB_PROJECT",
)
@click.option(
    "--assignee-id",
    help="User ID to assign the merge request",
    type=str,
    required=False,
    envvar="GITLAB_PROJECT",
)
def create_release_merge_request(
    url, token, source_branch, target_branch, project, assignee_id=None
):
    """
    Create a new merge request in a GitLab project. It is often used after the project release.
    """
    if not url:
        url = get_remote_url()
    if not project:
        project = get_remote_path()
    if not source_branch:
        from developers_chamber.git_utils import get_current_branch_name

        source_branch = get_current_branch_name()

    mr_url = create_merge_request_func(
        url=url,
        token=token,
        title=f'Merge branch "{source_branch}"',
        description="",
        source_branch=source_branch,
        target_branch=target_branch,
        project=project,
        assignee_id=assignee_id,
    )

    click.echo(f"Merge request was successfully created: {mr_url}")


@gitlab.command()
@click.option(
    "--url",
    help="GitLab instance API URL (defaults to gitlab.com)",
    type=str,
    required=False,
    envvar="GITLAB_URL",
    default=_default_gitlab_url,
)
@click.option(
    "--token",
    help="token (can be set as env variable GITLAB_TOKEN)",
    type=str,
    required=True,
    envvar="GITLAB_TOKEN",
)
@click.option("--source-branch", help="source Git branch", type=str)
@click.option(
    "--target-branch",
    help="Target Git branch (defaults to env variable GITLAB_TARGET_BRANCH)",
    type=str,
    envvar="GITLAB_TARGET_BRANCH",
    default="next",
)
@click.option(
    "--title",
    help="Merge request title",
    type=str,
    envvar="GITLAB_TARGET_BRANCH",
    default="next",
)
@click.option(
    "--project",
    help="GitLab project name (defaults to env variable GITLAB_PROJECT)",
    type=str,
    required=False,
    envvar="GITLAB_PROJECT",
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
    envvar="GITLAB_PROJECT",
)
@click.option(
    "--remove-source-branch",
    help="Remove the source branch once the merge request is merged",
    is_flag=True,
    default=False,
)
def create_merge_request(
    url,
    token,
    source_branch,
    target_branch,
    title,
    project,
    automerge,
    assignee_id=None,
    remove_source_branch=False,
):
    """
    Create a new merge request in a GitLab project. It is often used after the project release.
    """
    if not url:
        url = get_remote_url()
    if not project:
        project = get_remote_path()

    mr_url = create_merge_request_func(
        url=url,
        token=token,
        title=title,
        description="",
        source_branch=source_branch,
        target_branch=target_branch,
        project=project,
        assignee_id=assignee_id,
        automerge=automerge,
        remove_source_branch=remove_source_branch,
    )

    click.echo(f"Merge request was successfully created: {mr_url}")


@gitlab.command()
@click.option(
    "--url",
    help="GitLab instance API URL (defaults to gitlab.com)",
    type=str,
    required=False,
    envvar="GITLAB_URL",
    default=_default_gitlab_url,
)
@click.option(
    "--token",
    help="token (can be set as env variable GITLAB_TOKEN)",
    type=str,
    required=True,
    envvar="GITLAB_TOKEN",
)
@click.option(
    "--project",
    help="GitLab project name (defaults to env variable GITLAB_PROJECT)",
    type=str,
    required=False,
    envvar="GITLAB_PROJECT",
)
@click.option(
    "--merge-request-id",
    help="GitLab merge request ID",
    type=str,
    required=True,
)
def activate_merge_request_automerge(url, token, project, merge_request_id):
    """
    Create a new merge request in a GitLab project. It is often used after the project release.
    """
    if not url:
        url = get_remote_url()
    if not project:
        project = get_remote_path()

    message = activate_automerge_func(
        url=url, token=token, project=project, merge_request_id=merge_request_id
    )

    click.echo(f"{message}")


@gitlab.command()
@click.option(
    "--url",
    help="GitLab instance API URL (defaults to gitlab.com)",
    type=str,
    required=False,
    envvar="GITLAB_URL",
    default=_default_gitlab_url,
)
@click.option(
    "--token",
    help="token (can be set as env variable GITLAB_TOKEN)",
    type=str,
    required=True,
    envvar="GITLAB_TOKEN",
)
@click.option(
    "--project",
    help="GitLab project name (defaults to env variable GITLAB_PROJECT)",
    type=str,
    required=False,
    envvar="GITLAB_PROJECT",
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
def run_job(url, token, project, branch, variables):
    """
    Run a job in a GitLab project.
    """
    if not url:
        url = get_remote_url()
    if not project:
        project = get_remote_path()

    variables = (
        dict([var.split("=") for var in variables.split(",")]) if variables else {}
    )
    ci_job_url = run_job_func(url, token, project, f"refs/heads/{branch}", variables)

    click.echo(f"CI job was started: {ci_job_url}")


@gitlab.command()
@click.option(
    "--url",
    help="GitLab instance API URL (defaults to gitlab.com)",
    type=str,
    required=False,
    envvar="GITLAB_URL",
    default=_default_gitlab_url,
)
@click.option(
    "--token",
    help="token (can be set as env variable GITLAB_TOKEN)",
    type=str,
    required=True,
    envvar="GITLAB_TOKEN",
)
@click.option(
    "--project",
    help="GitLab project name (defaults to env variable GITLAB_PROJECT)",
    type=str,
    required=False,
    envvar="GITLAB_PROJECT",
)
def get_project_id(url, project, token):
    if not url:
        url = get_remote_url()
    if not project:
        project = get_remote_path()

    click.echo(get_project_id_func(url, project, token))


@gitlab.command()
@click.option(
    "--url",
    help="GitLab instance API URL (defaults to gitlab.com)",
    type=str,
    required=False,
    envvar="GITLAB_URL",
    default=_default_gitlab_url,
)
@click.option(
    "--token",
    help="token (can be set as env variable GITLAB_TOKEN)",
    type=str,
    required=False,
    envvar="GITLAB_TOKEN",
)
@click.option(
    "--job-token",
    help="CI job token, preferred over the private token (can be set as env variable "
    "CI_JOB_TOKEN)",
    type=str,
    required=False,
    envvar="CI_JOB_TOKEN",
)
@click.option(
    "--project",
    help="GitLab project name or ID (defaults to env variable GITLAB_PROJECT)",
    type=str,
    required=False,
    envvar="GITLAB_PROJECT",
)
@click.option(
    "--tag-name",
    help="name of the already pushed release tag (defaults to env variable CI_COMMIT_TAG)",
    type=str,
    required=True,
    envvar="CI_COMMIT_TAG",
)
@click.option(
    "--name",
    help='release name (defaults to the tag name, e.g. "lib-a@1.3.0" -> "lib-a 1.3.0")',
    type=str,
    required=False,
)
@click.option(
    "--description",
    help="release description, usually the CHANGELOG.md section of the released version",
    type=str,
    required=False,
)
@click.option(
    "--asset",
    "assets",
    help='link to a published artifact in the "name=URL" format (can be used repeatedly)',
    type=str,
    multiple=True,
)
def create_release_record(
    url, token, job_token, project, tag_name, name, description, assets
):
    """
    Create a GitLab release object for an already existing release tag.
    """
    if not token and not job_token:
        raise click.UsageError("GitLab token or job token is required")
    if not url:
        url = get_remote_url()
    if not project:
        project = get_remote_path()

    release_url = create_release_record_func(
        url=url,
        project=project,
        tag_name=tag_name,
        name=name,
        description=description,
        asset_links=parse_asset_links(assets),
        token=token,
        job_token=job_token,
    )

    click.echo(f"Release record was successfully created: {release_url}")
