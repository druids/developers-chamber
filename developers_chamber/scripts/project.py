import os

import click

from developers_chamber.click.options import ContainerDirToCopyType, ContainerCommandType
from developers_chamber.scripts import cli
from developers_chamber.project_utils import (
    set_hosts, compose_build, compose_run, compose_exec, compose_up, docker_clean, compose_install, compose_kill_all,
    compose_stop
)


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
default_containers_dir_to_copy = os.environ.get('PROJECT_DOCKER_COMPOSE_CONTAINERS_DIR_TO_COPY', '').split(',')
default_containers_install_command = os.environ.get('PROJECT_DOCKER_COMPOSE_CONTAINERS_INSTALL_COMMAND', '').split(',')


@cli.group()
def project():
    """Project commands"""


@project.command()
@click.option('--domain', '-d', help='Domain which will be set to the hosts file', type=str, required=True,
              multiple=True, default=default_domains)
def set_domain(domain):
    """
    Set local hostname translation to localhost
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
              type=ContainerDirToCopyType(), required=True, multiple=True, default=default_containers_dir_to_copy)
def build(project_name, compose_file, container, container_dir_to_copy):
    """
    Build docker container
    """
    compose_build(project_name, compose_file, container, container_dir_to_copy)


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
@click.pass_context
def run(ctx, project_name, compose_file, container, command):
    """
    Run one time command in docker container
    """
    compose_run(project_name, compose_file, container, ' '.join([command] + ctx.args))


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
@click.pass_context
def exec_command(ctx, project_name, compose_file, container, command):
    """
    Run command in docker service
    """
    compose_exec(project_name, compose_file, container, ' '.join([command] + ctx.args))


@project.command()
@click.option('--project-name', '-p', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose-file', '-f', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--container', '-c', help='Container name', type=str, required=False, multiple=True,
              default=default_up_containers)
@click.option('--all', '-a', 'all_containers', help='Run all container in compose file', default=False, is_flag=True)
def up(project_name, compose_file, container, all_containers):
    """
    Builds, (re)creates, starts, and attaches to containers for a service.
    """
    compose_up(project_name, compose_file, None if all_containers else container)


@project.command()
@click.option('--project-name', '-p', help='Name of the project', type=str, required=True, default=default_project_name)
@click.option('--compose-file', '-f', help='Compose file', type=str, required=True, multiple=True,
              default=default_compose_files)
@click.option('--container', '-c', help='Container name', type=str, required=False, multiple=True)
def stop(project_name, compose_file, container):
    """
    Stop containers.
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
    Builds, (re)creates, starts, and attaches to containers for a service.
    """
    compose_install(project_name, compose_file, var_dir, container_dir_to_copy, install_container_command)


@project.command()
def kill_all():
    """
    Kill all running docker instances
    """
    compose_kill_all()


@project.command()
@click.option('--hard', '-h', help='Clean hard', default=False, is_flag=True)
def clean(hard):
    """
    Clean docker images and its volumes
    """
    docker_clean(hard)
