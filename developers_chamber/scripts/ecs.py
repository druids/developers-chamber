import os
import sys

import click

from developers_chamber.ecs_utils import deploy_new_task_definition as deploy_new_task_func
from developers_chamber.ecs_utils import stop_service as stop_service_func
from developers_chamber.scripts import cli


default_region = os.environ.get('AWS_REGION')


@cli.command()
@click.option('--cluster', help='ecs cluster name', type=str, required=True)
@click.option('--service', help='ecs service names', type=str, required=True)
@click.option('--task-definition', help='ecs task definition name', type=str, required=True)
@click.option('--image', help='docker image tag to use', type=str, required=True)
@click.option('--region', help='aws region', type=str, default=default_region)
def ecs_deploy_new_task_definition(cluster, service, task_definition, image, region):
    """Deploy new task definition in AWS ECS."""
    if not region:
        raise click.BadParameter('region must not be empty')

    click.echo(deploy_new_task_func(cluster, service, task_definition, image, region))


@cli.command()
@click.option('--cluster', help='ecs cluster name', type=str, required=True)
@click.option('--service', help='ecs service name', type=str, required=True)
@click.option('--region', help='aws region', type=str, default=default_region)
def ecs_stop_service(cluster, service, region):
    """Stop an AWS ECS service by updating its size and setting it to 0."""
    if not region:
        raise click.BadParameter('region must not be empty')

    click.echo(stop_service_func(cluster, service, region))
