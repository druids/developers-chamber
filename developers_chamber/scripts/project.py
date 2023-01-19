import os
from datetime import date

import click

from developers_chamber.bitbucket_utils import get_commit_builds
from developers_chamber.click.options import (ContainerCommandType,
                                              ContainerDirToCopyType,
                                              ContainerEnvironment)
from developers_chamber.git_utils import create_branch as create_branch_func
from developers_chamber.git_utils import (get_commit_hash,
                                          get_current_branch_name)
from developers_chamber.jira_utils import get_branch_name
from developers_chamber.project_utils import (compose_build, compose_exec,
                                              compose_install,
                                              compose_kill_all, compose_run,
                                              compose_stop, compose_up,
                                              copy_containers_dirs as copy_containers_dirs_func)
from developers_chamber.project_utils import bind_library as bind_library_func

from developers_chamber.project_utils import \
    create_or_update_pull_request as create_or_update_pull_request_func
from developers_chamber.project_utils import (docker_clean, set_hosts,
                                              start_task, stop_task,
                                              sync_timer_to_jira)
from developers_chamber.scripts import cli

default_project_name = os.environ.get('PROJECT_DOCKER_COMPOSE_PROJECT_NAME')
default_compose_files = (
    os.environ.get('PROJECT_DOCKER_COMPOSE_FILES').split(',')
    if os.environ.get('PROJECT_DOCKER_COMPOSE_FILES') else None
)
default_domains = (
    os.environ.get('PROJECT_DOMAINS').split(',')
    if os.environ.get('PROJECT_DOMAINS') else None
)
default_containers = (
    os.environ.get('PROJECT_DOCKER_COMPOSE_CONTAINERS').split(',')
    if os.environ.get('PROJECT_DOCKER_COMPOSE_CONTAINERS') else None
)
default_up_containers = (
    os.environ.get('PROJECT_DOCKER_COMPOSE_DEFAULT_UP_CONTAINERS').split(',')
    if os.environ.get('PROJECT_DOCKER_COMPOSE_DEFAULT_UP_CONTAINERS') else None
)
default_var_dirs = (
    os.environ.get('PROJECT_DOCKER_COMPOSE_VAR_DIRS').split(',')
    if os.environ.get('PROJECT_DOCKER_COMPOSE_VAR_DIRS') else None
)
default_containers_dir_to_copy = (
    os.environ.get('PROJECT_DOCKER_COMPOSE_CONTAINERS_DIR_TO_COPY').split(',')
    if os.environ.get('PROJECT_DOCKER_COMPOSE_CONTAINERS_DIR_TO_COPY') else None
)
default_containers_install_command = os.environ.get('PROJECT_DOCKER_COMPOSE_CONTAINERS_INSTALL_COMMAND', '').split(',')
default_library_dir = os.environ.get('PROJECT_LIBRARY_DIR')

jira_url = os.environ.get('JIRA_URL')
jira_username = os.environ.get('JIRA_USERNAME')
jira_api_key = os.environ.get('JIRA_API_KEY')
jira_project_key = os.environ.get('JIRA_PROJECT_KEY')

toggl_api_key = os.environ.get('TOGGL_API_KEY')
toggl_project_id = os.environ.get('TOGGL_PROJECT_ID')
toggl_workspace_id = os.environ.get('TOGGL_WORKSPACE_ID')

source_branch_name = os.environ.get('PROJECT_SOURCE_BRANCH_NAME', 'next')
bitbucket_username = os.environ.get('BITBUCKET_USERNAME')
bitbucket_password = os.environ.get('BITBUCKET_PASSWORD')
bitbucket_destination_branch_name = os.environ.get('BITBUCKET_BRANCH_NAME', 'next')
bitbucket_repository_name = os.environ.get('BITBUCKET_REPOSITORY')


@cli.group()
def project():
    """Main helpers for a whole project management."""


@project.command()
@click.option('--domain', '-d', help='Domain which will be set to the hosts file', type=str, required=True,
              multiple=True, default=default_domains)
def set_domain(domain):
    """
    Set local hostname translation to localhost. It updates /etc/hosts headers according to input domain.
    """
    set_hosts(domain)
    click.echo(
        'Host file was set: {} -> 127.0.0.1'.format(', '.join(domain))
    )


@project.command()
@click.option('--project-name', '-p', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose-file', '-f', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--container', '-c', help='Container name', type=str, required=False, multiple=True)
@click.option('--container-dir-to-copy', '-d',
              help='Container dir which will be copied after build in format '
                   'DOCKER_CONTAINER_NAME:CONTAINER_DIRECTORY:HOST_DIRECTORY',
              type=ContainerDirToCopyType(), multiple=True, default=default_containers_dir_to_copy)
@click.option('--env', 'env', help='Environment variables', type=ContainerEnvironment(), default=None)
def build(project_name, compose_file, container, container_dir_to_copy, env):
    """
    Build docker container via compose file and name it with the project name.
    Command is able to copy data from the container built image to the host directory.
    This can help if we need to share installed python libraries with the host (for example for the pycharm)
    """
    compose_build(project_name, compose_file, container, container_dir_to_copy, env=env)


@project.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True
    )
)
@click.argument('command')
@click.option('--project-name', '-p', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose-file', '-f', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--container', '-c', help='Container name', type=str, required=True, multiple=True,
              default=default_containers[:1] if default_containers else None)
@click.option('--env', 'env', help='Environment variables', type=ContainerEnvironment(), default=None)
@click.pass_context
def run(ctx, project_name, compose_file, container, command, env):
    """
    Run one time command on docker container defined in compose file. You can specify image environment variables.
    """
    compose_run(project_name, compose_file, container, ' '.join([command] + ctx.args), env=env)


@project.command(
    name='exec',
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True
    )
)
@click.argument('command')
@click.option('--project-name', '-p', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose-file', '-c', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--container', '-c', help='Container name', type=str, required=True, multiple=True,
              default=default_containers[:1] if default_containers else None)
@click.option('--env', 'env', help='Environment variables', type=ContainerEnvironment(), default=None)
@click.pass_context
def exec_command(ctx, project_name, compose_file, container, command, env):
    """
    Run command on already executed docker container defined in compose file.
    You can specify image environment variables.
    """
    compose_exec(project_name, compose_file, container, ' '.join([command] + ctx.args), env=env)


@project.command()
@click.option('--project-name', '-p', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose-file', '-f', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--container', '-c', help='Container name', type=str, required=False, multiple=True,
              default=default_up_containers)
@click.option('--all', '-a', 'all_containers', help='Run all container in compose file', default=False, is_flag=True)
@click.option('--env', 'env', help='Environment variables', type=ContainerEnvironment(), default=None)
def up(project_name, compose_file, container, all_containers, env):
    """
    Builds, (re)creates, starts, and attaches to containers for a service defined in compose file.
    """
    compose_up(project_name, compose_file, None if all_containers else container, env=env)


@project.command()
@click.option('--project-name', '-p', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose-file', '-f', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--container', '-c', help='Container name', type=str, required=False, multiple=True)
def stop(project_name, compose_file, container):
    """
    Stop all the docker containers from the compose file.
    """
    compose_stop(project_name, compose_file, container)


@project.command()
@click.option('--project-name', '-p', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose-file', '-f', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--var-dir', '-v', help='Variable content directory', type=str, required=True,
              default=default_var_dirs, multiple=True)
@click.option('--container-dir-to-copy', '-d',
              help='Container dir which will be copied after build in format '
                   'DOCKER_CONTAINER_NAME:CONTAINER_DIRECTORY:HOST_DIRECTORY',
              type=ContainerDirToCopyType(), required=True, multiple=True, default=default_containers_dir_to_copy)
@click.option('--install-container-command', '-m',
              help='Container command which will be run after build in format DOCKER_CONTAINER_NAME:COMMAND',
              type=ContainerCommandType(), required=False, multiple=True, default=default_containers_install_command)
def install(project_name, compose_file, var_dir, container_dir_to_copy, install_container_command):
    """
    Builds, (re)creates, starts, and attaches to containers for a service defined in compose file.
    """
    compose_install(project_name, compose_file, var_dir, container_dir_to_copy, install_container_command)


@project.command()
@click.option('--project-name', '-p', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--container-dir-to-copy', '-d',
              help='Container dir which will be copied after build in format '
                   'DOCKER_CONTAINER_NAME:CONTAINER_DIRECTORY:HOST_DIRECTORY',
              type=ContainerDirToCopyType(), required=False, multiple=True, default=default_containers_dir_to_copy)
def copy_container_dirs(project_name, container_dir_to_copy):
    """
    Copy directories from a docker image to the host.
    """
    copy_containers_dirs_func(project_name, container_dir_to_copy)


@project.command()
@click.option('--library-source-dir', '-s', help='Library source directory', type=str, required=True)
@click.option('--library-destination-dir', '-d', help='Library destination directory', type=str, required=True,
              default=default_library_dir)
def bind_library(library_source_dir, library_destination_dir):
    """
    Mount a directory to an another location on docker host with bindfs.
    It can be used for bind python library to the project site packages shared with volumes to the docker container.
    """
    bind_library_func(library_source_dir, library_destination_dir)


@project.command()
def kill_all():
    """
    Kill all running docker instances.
    """
    compose_kill_all()


@project.command()
@click.option('--all', '-a', help='Clean all images and volumes', default=False, is_flag=True)
def clean(all):
    """
    Clean docker images and its volumes. If you want to clean all the images and volumes use parameter -a.
    """
    docker_clean(all)


@project.group()
def task():
    """Helpers to work with project task in Jira and Toggle"""


@task.command()
@click.option('--jira-url',  help='Jira URL', type=str, required=True, default=jira_url)
@click.option('--jira-username',  help='Jira username', type=str, required=True, default=jira_username)
@click.option('--jira-api-key',  help='Jira API key/password', type=str, required=True, default=jira_api_key)
@click.option('--jira_project-key',  help='Jira project key', type=str, required=False, default=jira_project_key)
@click.option('--toggl-api-key', help='toggle API key', type=str, required=True, default=toggl_api_key)
@click.option('--toggl-workspace-id', '-w',  help='toggl workspace ID', type=str, required=False,
              default=toggl_workspace_id)
@click.option('--toggl-project-id', '-p',  help='toggl project ID', type=str, required=False, default=toggl_project_id)
@click.option('--issue-key', '-i',  help='key of the task', type=str)
def start(jira_url, jira_username, jira_api_key, jira_project_key, toggl_api_key, toggl_workspace_id, toggl_project_id,
          issue_key):
    """
    Get information from Jira about issue and start Toggle timer.
    """
    click.echo(start_task(jira_url, jira_username, jira_api_key, jira_project_key, toggl_api_key, toggl_workspace_id,
                          toggl_project_id, issue_key))


@task.command()
@click.option('--jira-url', help='Jira URL', type=str, required=True, default=jira_url)
@click.option('--jira-username', help='Jira username', type=str, required=True, default=jira_username)
@click.option('--jira-api-key', help='Jira API key/password', type=str, required=True, default=jira_api_key)
@click.option('--toggl-api-key', help='toggle API key', type=str, required=True, default=toggl_api_key)
def stop(jira_url, jira_username, jira_api_key, toggl_api_key):
    """
    Stop Toggle timer and logs time to the Jira issue.
    """
    click.echo(stop_task(jira_url, jira_username, jira_api_key, toggl_api_key))


@task.command()
@click.option('--jira-url',  help='Jira URL', type=str, required=True, default=jira_url)
@click.option('--jira-username', help='Jira username', type=str, required=True, default=jira_username)
@click.option('--jira-api-key', help='Jira API key/password', type=str, required=True, default=jira_api_key)
@click.option('--jira-project-key',  help='Jira project key', type=str, required=False, default=jira_project_key)
@click.option('--source_branch_name', '-s', help='source branch name', type=str, default=source_branch_name)
@click.option('--issue-key', '-i',  help='key of the task', type=str, required=True)
def create_branch_from_issue(jira_url, jira_username, jira_api_key, project_key, source_branch_name, issue_key):
    """
    Create a new git branch from the source branch with name generated from the Jira issue.
    """
    click.echo('Branch "{}" was created'.format(
        create_branch_func(
            source_branch_name, get_branch_name(jira_url, jira_username, jira_api_key, issue_key, project_key)
        )
    ))


@task.command()
@click.option('--jira-url', '-u',  help='Jira URL', type=str, required=True, default=jira_url)
@click.option('--jira-username', '-a',  help='Jira username', type=str, required=True, default=jira_username)
@click.option('--jira-api-key', '-p',  help='Jira API key/password', type=str, required=True, default=jira_api_key)
@click.option('--bitbucket-username', help='username', type=str, required=True, default=bitbucket_username)
@click.option('--bitbucket-password', help='password', type=str, required=True,
              default=bitbucket_password)
@click.option('--bitbucket-destination-branch-name', help='destination bitbucket branch name', type=str, required=True,
              default=bitbucket_destination_branch_name)
@click.option('--bitbucket-repository-name', '-r', help='bitbucket repository name', type=str, required=True,
              default=bitbucket_repository_name)
def create_or_update_pull_request(jira_url, jira_username, jira_api_key, bitbucket_username, bitbucket_password,
                                  bitbucket_destination_branch_name, bitbucket_repository_name):
    """
    Create a Bitbucket pull request named according to the Jira issue.
    """
    click.echo('Pull request "{}" was created or updated'.format(
        create_or_update_pull_request_func(
            jira_url, jira_username, jira_api_key, bitbucket_username, bitbucket_password,
            bitbucket_destination_branch_name, bitbucket_repository_name
        )
    ))


@task.command()
@click.option('--jira-url', help='Jira URL', type=str, required=True, default=jira_url)
@click.option('--jira-username', help='Jira username', type=str, required=True, default=jira_username)
@click.option('--jira-api-key', help='Jira API key/password', type=str, required=True, default=jira_api_key)
@click.option('--toggl-api-key', help='toggle API key', type=str, required=True, default=toggl_api_key)
@click.option('--toggl-workspace-id', '-w',  help='toggl workspace ID', type=str, required=False,
              default=toggl_workspace_id)
@click.option('--toggl-project-id', '-p',  help='toggl project ID', type=str, required=False, default=toggl_project_id)
@click.option('--from-date', '-f',  help='report from', type=click.DateTime(formats=["%Y-%m-%d"]),
              default=str(date.today()))
@click.option('--to-date', '-t',  help='report to', type=click.DateTime(formats=["%Y-%m-%d"]),
              default=str(date.today()))
def sync_timer_log_to_issues(jira_url, jira_username, jira_api_key, toggl_api_key, toggl_workspace_id,
                             toggl_project_id, from_date, to_date):
    """
    Synchronize logged time in Toggle timer with issues worklog in Jira.
    """
    sync_timer_to_jira(jira_url, jira_username, jira_api_key, toggl_api_key, toggl_workspace_id, toggl_project_id,
                       from_date.date(), to_date.date())
    click.echo('Issue times were synchronized with the timer')


@task.command()
@click.option('--bitbucket-username', help='username', type=str, required=True, default=bitbucket_username)
@click.option('--bitbucket-password', help='password', type=str, required=True,
              default=bitbucket_password)
@click.option('--bitbucket-repository-name', '-r', help='bitbucket repository name', type=str, required=True,
              default=bitbucket_repository_name)
@click.option('--branch-name', help='git branch name', type=str, required=False)
def print_last_commit_build(bitbucket_username, bitbucket_password,
                            bitbucket_repository_name, branch_name):
    """
    Print the last commit test results in Bitbucket of the selected branch.
    """
    branch_name = branch_name or get_current_branch_name()
    commit_builds = get_commit_builds(
        bitbucket_username, bitbucket_password, bitbucket_repository_name, get_commit_hash(branch_name)
    )
    if commit_builds:
        for build_data in commit_builds:
            click.echo(build_data['name'])
            click.echo('  Description: {}'.format(build_data['description']))
            click.echo('  URL: {}\n'.format(build_data['url']))
    else:
        click.echo('Builds weren\'t found')
