import os

import click

from developers_chamber.ecs_utils import deploy_new_task_definition as deploy_new_task_definition_func
from developers_chamber.ecs_utils import get_services_names as get_services_names_func
from developers_chamber.ecs_utils import get_task_definition_for_service as get_task_definition_for_service_func
from developers_chamber.ecs_utils import get_tasks_for_service as get_tasks_for_service_func
from developers_chamber.ecs_utils import redeploy_cluster_services as redeploy_cluster_services_func
from developers_chamber.ecs_utils import redeploy_services as redeploy_services_func
from developers_chamber.ecs_utils import register_new_task_definition as register_new_task_definition_func
from developers_chamber.ecs_utils import run_fargate_debug as run_fargate_debug_func
from developers_chamber.ecs_utils import run_service_task as run_service_task_func
from developers_chamber.ecs_utils import run_task as run_task_func
from developers_chamber.ecs_utils import run_task_and_wait_for_success as run_task_and_wait_for_success_func
from developers_chamber.ecs_utils import start_cluster_services as start_cluster_services_func
from developers_chamber.ecs_utils import start_service as start_service_func
from developers_chamber.ecs_utils import start_services as start_services_func
from developers_chamber.ecs_utils import stop_service as stop_service_func
from developers_chamber.ecs_utils import \
    stop_service_and_wait_for_tasks_to_stop as stop_service_and_wait_for_tasks_to_stop_func
from developers_chamber.ecs_utils import \
    stop_services_and_wait_for_tasks_to_stop as stop_services_and_wait_for_tasks_to_stop_func
from developers_chamber.ecs_utils import \
    update_service_to_latest_task_definition as update_service_to_latest_task_definition_func
from developers_chamber.ecs_utils import wait_for_services_stable as wait_for_services_stable_func
from developers_chamber.scripts import cli

default_region = os.environ.get('AWS_REGION')
default_cluster = os.environ.get('AWS_ECS_CLUSTER')


@cli.group()
def ecs():
    """Helpers for AWS ECS management."""


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service names', type=str, required=True)
@click.option('--task-definition', '-t', help='ECS task definition name', type=str, required=True)
@click.option('--images', '-i', help='JSON containing containers and their images', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def deploy_new_task_definition(cluster, service, task_definition, images, region):
    """
    Deploy new task definition in AWS ECS. This command also updates the service and forces new deployment.
    """
    deploy_new_task_definition_func(cluster, service, task_definition, images, region)


@ecs.command()
@click.option('--task-definition', '-t', help='ECS task definition name', type=str, required=True)
@click.option('--images', '-i', help='JSON containing containers and their images', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def register_new_task_definition(task_definition, images, region):
    """
    Register new task definition in AWS ECS.
    """
    click.echo(register_new_task_definition_func(task_definition, images, region))


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service names', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def update_service_to_latest_task_definition(cluster, service, region):
    """
    Update service with the latest available task_definition.
    """
    update_service_to_latest_task_definition_func(cluster, service, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def stop_service(cluster, service, region):
    """
    Stop an AWS ECS service by updating its desiredCount to 0.
    """
    stop_service_func(cluster, service, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--count', '-o', help='Desired count for service', type=int)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def start_service(cluster, service, count, region):
    """
    Start an AWS ECS service by updating its desiredCount to 0.
    """
    start_service_func(cluster, service, count, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--count', '-o', help='Desired count for service', type=int)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def start_cluster_services(cluster, count, region):
    """
    Start an AWS ECS service by updating its desiredCount to 0.
    """
    start_cluster_services_func(cluster, count, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--services', '-s', help='ECS services names divided by comma', type=str, required=True)
@click.option('--count', '-o', help='Desired count for service', type=int)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def start_services(cluster, services, count, region):
    """
    Start an AWS ECS service by updating its desiredCount to 0.
    """
    services = services.split(',')
    start_services_func(cluster, services, count, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--task-definition', '-t', help='ECS task definition name', type=str, required=True)
@click.option('--command', '-m', help='command to run', type=str, default=None)
@click.option('--name', '-n', help='ECS task name', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def run_task(cluster, task_definition, command, name, region):
    """
    Run a single task in AWS ECS.
    """
    run_task_func(cluster, task_definition, command, name, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--task-definition', '-t', help='ECS task definition name', type=str, required=True)
@click.option('--command', '-m', help='command to run', type=str, default=None)
@click.option('--name', '-n', help='ECS task name', type=str, required=True)
@click.option('--success-string', help='String that is considered a success', type=str, default='0', required=True)
@click.option('--timeout', '-o', help='Seconds to wait before exiting with fail state', type=int, default=600)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def run_task_and_wait_for_success(cluster, task_definition, command, name, success_string, timeout, region):
    """
    Run a single task in AWS ECS and wait for it to stop with success.
    """
    run_task_and_wait_for_success_func(cluster, task_definition, command, name, success_string, timeout, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--command', '-m', help='command to run', type=str, required=True)
@click.option('--success-string', help='String that is considered a success code', type=str, default='0', required=True)
@click.option('--timeout', '-o', help='Seconds to wait before exiting with fail state', type=int, default=600)
@click.option('--container', '-f', help='Container name to run the command in', type=str, default=None)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def run_service_task(cluster, service, command, success_string, timeout, region, container):
    """
    Run a single task based on service's task definition in AWS ECS and wait for it to stop with success.
    """
    run_service_task_func(cluster, service, command, success_string, timeout, region, container)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--command', '-m', help='command to run', type=str, required=True)
@click.option('--success-string', help='String that is considered a success code', type=str, default='0', required=True)
@click.option('--timeout', '-o', help='Seconds to wait before exiting with fail state', type=int, default=600)
@click.option('--container', '-f', help='Container name to run the command in', type=str, default=None)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
@click.option('--subnet', help='subnet ID', type=str, required=True, multiple=True)
@click.option('--security-group', help='security group ID', type=str, required=True, multiple=True)
@click.option('--environment-file', '-e', help='S3 arn with path to env file', type=str, required=False, default=None)
def run_service_task_fargate(cluster, service, command, success_string, timeout, region, container, subnet, security_group, environment_file):
    """
    Run a single task based on service's task definition in AWS ECS and wait for it to stop with success.
    """
    run_service_task_func(cluster, service, command, success_string, timeout, region, container, networkConfiguration={
        'awsvpcConfiguration': {
            'subnets': [s for s in subnet],
            'securityGroups': [s for s in security_group],
            'assignPublicIp': 'DISABLED'
        }
    }, launchType='FARGATE', environmentFiles=environment_file)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def get_tasks_for_service(cluster, service, region):
    """
    Return list of tasks running under specified service.
    """
    click.echo(get_tasks_for_service_func(cluster, service, region))


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def get_task_definition_for_service(cluster, service, region):
    """
    Return task definition arn for specified service.
    """
    click.echo(get_task_definition_for_service_func(cluster, service, region))


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--service', '-s', help='ECS service name', type=str, required=True)
@click.option('--timeout', '-o', help='Seconds to wait before exiting with fail state', type=int, default=600)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def stop_service_and_wait_for_tasks_to_stop(cluster, service, timeout, region):
    """
    Stop service and wait for the tasks to stop.
    """
    stop_service_and_wait_for_tasks_to_stop_func(cluster, service, timeout, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--services', '-s', help='ECS services names separated by comma', type=str, required=True)
@click.option('--timeout', '-o', help='Seconds to wait before exiting with fail state', type=int, default=600)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def stop_services_and_wait_for_tasks_to_stop(cluster, services, timeout, region):
    """
    Stop services and wait for the tasks to stop.
    """
    services = services.split(',')
    stop_services_and_wait_for_tasks_to_stop_func(cluster, services, timeout, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def get_services_names(cluster, region):
    """
    Get names of the cluster services.
    """
    for service_name in get_services_names_func(cluster, region):
        click.echo(service_name)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--services', '-s', help='ECS services names divided by comma', type=str, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def redeploy_services(cluster, services, region):
    """
    Redeploy services by forcing new service deployment.
    """
    services = services.split(',')
    redeploy_services_func(cluster, services, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def redeploy_cluster_services(cluster, region):
    """
    Redeploy all cluster services by forcing new service deployment.
    """
    redeploy_cluster_services_func(cluster, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
def wait_for_services_stable(cluster, region):
    """
    Wait until all non-daemon services in cluster are stable.
    """
    wait_for_services_stable_func(cluster, region)


@ecs.command()
@click.option('--cluster', '-c', help='ECS cluster name', type=str, default=default_cluster, required=True)
@click.option('--region', '-r', help='AWS region', type=str, default=default_region, required=True)
@click.option('--task-definition', '-t', help='Task definition name', type=str, required=True)
@click.option('--network-configuration-ssm-parameter', '-n', help='Name of SSM parameter with network configuration for the task', type=str, required=True)
def run_fargate_debug(cluster, region, task_definition, network_configuration_ssm_parameter):
    """
    Run a debug Fargate task (internal access to databases etc.)
    """
    run_fargate_debug_func(cluster, region, task_definition, network_configuration_ssm_parameter)
