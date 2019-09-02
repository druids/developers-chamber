import os

import click

from developers_chamber.ecs_utils import deploy_new_task_definition as deploy_new_task_func
from developers_chamber.ecs_utils import run_task as run_task_func
from developers_chamber.ecs_utils import stop_service as stop_service_func
from developers_chamber.scripts import cli


default_region = os.environ.get('AWS_REGION')


@cli.group()
def ecs():
    """ECS commands"""


@ecs.command()
@click.option('--cluster', help='ECS cluster name', type=str, required=True)
@click.option('--service', help='ECS service names', type=str, required=True)
@click.option('--task-definition', help='ECS task definition name', type=str, required=True)
@click.option('--image', help='docker image tag to use', type=str, required=True)
@click.option('--region', help='AWS region', type=str, default=default_region, required=True)
def deploy_new_task_definition(cluster, service, task_definition, image, region):
    """Deploy new task definition in AWS ECS."""
    click.echo(deploy_new_task_func(cluster, service, task_definition, image, region))


@ecs.command()
@click.option('--cluster', help='ECS cluster name', type=str, required=True)
@click.option('--service', help='ECS service name', type=str, required=True)
@click.option('--region', help='AWS region', type=str, default=default_region, required=True)
def stop_service(cluster, service, region):
    """Stop an AWS ECS service by updating its size and setting it to 0."""
    click.echo(stop_service_func(cluster, service, region))


@ecs.command()
@click.option('--cluster', help='ECS cluster name', type=str, required=True)
@click.option('--task-definition', help='ECS task definition name', type=str, required=True)
@click.option('--command', help='command to run', type=str, required=True)
@click.option('--name', help='ECS task name', type=str, required=True)
@click.option('--region', help='AWS region', type=str, default=default_region, required=True)
def run_task(cluster, task_definition, command, name, region):
    """Run a single task in AWS ECS."""
    click.echo(run_task_func(cluster, task_definition, command, name, region))
