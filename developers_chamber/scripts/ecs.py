import os
import click

from developers_chamber.ecs_utils import deploy_new_task_definition as deploy_new_task_definition_func
from developers_chamber.ecs_utils import run_task as run_task_func
from developers_chamber.ecs_utils import stop_service as stop_service_func
from developers_chamber.ecs_utils import start_service as start_service_func
from developers_chamber.ecs_utils import register_new_task_definition as register_new_task_definition_func
from developers_chamber.ecs_utils import update_service_to_latest_task_definition as \
    update_service_to_latest_task_definition_func
from developers_chamber.ecs_utils import run_task_and_wait_for_success as run_task_and_wait_for_success_func
from developers_chamber.ecs_utils import get_tasks_for_service as get_tasks_for_service_func
from developers_chamber.ecs_utils import get_task_definition_for_service as get_task_definition_for_service_func
from developers_chamber.ecs_utils import stop_service_and_wait_for_tasks_to_stop as \
    stop_service_and_wait_for_tasks_to_stop_func
from developers_chamber.ecs_utils import migrate_service as migrate_service_func
from developers_chamber.scripts import cli


default_region = os.environ.get('AWS_REGION')
default_cluster = os.environ.get('AWS_ECS_CLUSTER')

@cli.group()
def ecs():
    """ECS commands"""


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service names', type=str, required=True)
@click.option('--task-definition', '-t', help='ECS task definition name', type=str, required=True)
@click.option('--image', '-i', help='docker image:tag to use', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def deploy_new_task_definition(cluster, service, task_definition, image, region):
    """Deploy new task definition in AWS ECS. This command also updates the service and forces new deployment."""
    deploy_new_task_definition_func(cluster, service, task_definition, image, region)


@ecs.command()
@click.option('--task-definition', '-t', help='ECS task definition name', type=str, required=True)
@click.option('--image', '-i', help='docker image:tag to use', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def register_new_task_definition(task_definition, image, region):
    """Register new task definition in AWS ECS."""
    click.echo(register_new_task_definition_func(task_definition, image, region))


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service names', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def update_service_to_latest_task_definition(cluster, service, region):
    """Update service with the latest available task_definition"""
    update_service_to_latest_task_definition_func(cluster, service, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def stop_service(cluster, service, region):
    """Stop an AWS ECS service by updating its desiredCount to 0."""
    stop_service_func(cluster, service, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--count', '-o', help='Desired count for service', type=int, default=1, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def start_service(cluster, service, count, region):
    """Start an AWS ECS service by updating its desiredCount to 0."""
    start_service_func(cluster, service, count, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--task-definition', '-t', help='ECS task definition name', type=str, required=True)
@click.option('--command', '-m', help='command to run', type=str, required=True)
@click.option('--name', '-n', help='ECS task name', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def run_task(cluster, task_definition, command, name, region):
    """Run a single task in AWS ECS."""
    run_task_func(cluster, task_definition, command, name, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--task-definition', '-t', help='ECS task definition name', type=str, required=True)
@click.option('--command', '-m', help='command to run', type=str, default=None)
@click.option('--name', '-n', help='ECS task name', type=str, required=True)
@click.option('--success-string', help='String that is considered a success', type=str, default='0', required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def run_task_and_wait_for_success(cluster, task_definition, command, name, success_string, region):
    """Run a single task in AWS ECS and wait for it to stop with success."""
    run_task_and_wait_for_success_func(cluster, task_definition, command, name, success_string, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--command', '-m', help='command to run', type=str, required=True)
@click.option('--success-string', help='String that is considered a success code', type=str, default='0', required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def migrate_service(cluster, service, command, success_string, region):
    """Run a single task based on service's task definition in AWS ECS and wait for it to stop with success."""
    migrate_service_func(cluster, service, command, success_string, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def get_tasks_for_service(cluster, service, region):
    """ Return list of tasks running under specified service """
    click.echo(get_tasks_for_service_func(cluster, service, region))


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def get_task_definition_for_service(cluster, service, region):
    """ Return task definition arn for specified service """
    click.echo(get_task_definition_for_service_func(cluster, service, region))


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def stop_service_and_wait_for_tasks_to_stop(cluster, service, region):
    """ Stop service and wait for the tasks to stop """
    stop_service_and_wait_for_tasks_to_stop_func(cluster, service, region)

