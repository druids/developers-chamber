import os

import click

from developers_chamber.scripts import cli
from developers_chamber.docker_utils import build as build_func


default_project_name = os.environ.get('DOCKER_PROJECT_NAME')
default_docker_compose_files = (
    os.environ.get('DOCKER_COMPOSE_FILES').split(',') if 'DOCKER_COMPOSE_FILES' in os.environ else None
)


@cli.group()
def docker():
    """Docker and docker-compose commands"""


@docker.command()
@click.option('--project-name', help='name of the projecte',type=str, default=default_project_name, required=True)
@click.option('--file',  help='docker compose file', type=str, default=default_docker_compose_files, required=True,
              multiple=True)
@click.option('--no-cache',  help='docker compose turn off cache', type=bool, default=False, required=True)
def build(project_name, file, no_cache):
    """
    Build docker images according to docker configuration
    """
    print(file)
    build_func(project_name, file, no_cache)

