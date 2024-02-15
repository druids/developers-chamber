import json
import logging
import time
from datetime import datetime
from multiprocessing.pool import ThreadPool

import boto3
from botocore.client import Config
from botocore.credentials import subprocess
from botocore.exceptions import ClientError, WaiterError
from click import ClickException

from developers_chamber.utils import call_command

LOGGER = logging.getLogger()


def _get_ecs_client(region):
    return boto3.client(
        'ecs',
        config=Config(region_name=region),
    )


def _get_logs_client(region):
    return boto3.client(
        'logs',
        config=Config(region_name=region),
    )


def _get_autoscaling_client(region):
    return boto3.client(
        'application-autoscaling',
        config=Config(region_name=region),
    )

def _get_ssm_client(region):
    return boto3.client(
        'ssm',
        config=Config(region_name=region),
    )

def get_log_events(log_group, log_stream, region):
    logs_client = _get_logs_client(region)

    try:
        resp = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            limit=10000,
        )
        return resp['events']

    except ClientError as ex:
        raise ClickException(str(ex))


def register_new_task_definition(task_definition_name, images, region, ecs_client=None):
    try:
        images_data = json.loads(images)
    except json.JSONDecodeError as ex:
        raise ClickException(ex)
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    try:
        old_task_definition = ecs_client.describe_task_definition(
            taskDefinition=task_definition_name,
            include=[
                'TAGS',
            ],
        )
    except ClientError as ex:
        raise ClickException(ex)

    LOGGER.info('Images: %s', images_data)
    LOGGER.info('Old task definition ARN: %s', old_task_definition['taskDefinition']['taskDefinitionArn'])

    definition = old_task_definition['taskDefinition']
    for container_definition in definition['containerDefinitions']:
        try:
            container_definition['image'] = images_data[container_definition['name']]
        except KeyError as ex:
            LOGGER.warning('Using previous image "%s" for container definition "%s"', container_definition['image'],
                           container_definition['name'])

    new_task_definition = {
        'containerDefinitions': definition['containerDefinitions'],
        'executionRoleArn': definition['executionRoleArn'],
        'family': definition['family'],
        'networkMode': definition['networkMode'],
        'requiresCompatibilities': definition['requiresCompatibilities'],
        'tags': old_task_definition['tags'],
        'taskRoleArn': definition['taskRoleArn'],
        'volumes': definition['volumes'],
    }

    if 'cpu' in definition:
        new_task_definition['cpu'] = definition['cpu']
    if 'memory' in definition:
        new_task_definition['memory'] = definition['memory']

    try:
        response = ecs_client.register_task_definition(**new_task_definition)
    except ClientError as ex:
        raise ClickException(ex)

    new_task_definition_arn = response['taskDefinition']['taskDefinitionArn']
    LOGGER.info('New task definition ARN: %s', new_task_definition_arn)

    return new_task_definition_arn


def get_task_definition_for_service(cluster, service, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    try:
        services = ecs_client.describe_services(
            cluster=cluster,
            services=[service],
        )
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except ClientError as ex:
        raise ClickException(ex)

    number_of_services = len(services['services'])

    if number_of_services > 1:
        raise ClickException(
            'More than one service with the same name found: {}'.format(len(services['services']))
        )
    elif number_of_services == 0:
        raise ClickException("Service not found: '{}'".format(service))

    return services['services'][0]['taskDefinition']


def update_service_to_latest_task_definition(cluster, service, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    old_task_definition = get_task_definition_for_service(
        cluster=cluster, service=service, region=region, ecs_client=ecs_client)
    LOGGER.info('Current task definition ARN: {}'.format(old_task_definition))

    try:
        new_task_definition = ecs_client.describe_task_definition(
            taskDefinition=old_task_definition[:old_task_definition.rfind(':')]
        )
    except ClientError as ex:
        raise ClickException(ex)

    new_task_definition_arn = new_task_definition['taskDefinition']['taskDefinitionArn']
    LOGGER.info('New task definition ARN: {}'.format(new_task_definition_arn))

    update_service_to_new_task_definition(
        cluster=cluster,
        service=service,
        task_definition=new_task_definition_arn,
        region=region,
        ecs_client=ecs_client,
    )


def update_service_to_new_task_definition(cluster, service, task_definition, region, force=True, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    try:
        response = ecs_client.update_service(
            cluster=cluster,
            service=service,
            taskDefinition=task_definition,
            forceNewDeployment=force,
        )
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except ecs_client.exceptions.ServiceNotFoundException:
        raise ClickException("Service not found: '{}'".format(service))
    except ClientError as ex:
        raise ClickException(ex)


def deploy_new_task_definition(cluster, service, task_definition, images, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    new_task_definition = register_new_task_definition(
        task_definition=task_definition, images=images, region=region, ecs_client=ecs_client,
    )

    update_service_to_new_task_definition(
        cluster=cluster,
        service=service,
        task_definition=new_task_definition,
        region=region,
        ecs_client=ecs_client,
    )


def start_service(cluster, service, count, region, ecs_client=None, as_client=None):
    if count is not None and count < 1:
        raise ClickException("Count must be greater than zero or 'None' to be determined from autoscaling targets.")

    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    if count is None:
        try:
            count = get_min_capacity_for_service(cluster=cluster, service=service, region=region)
        except ClickException as ex:
            raise ClickException(
                'Set explicit count or set up autoscaling with minimum capacity.\n{}'.format(ex)
            )

    LOGGER.info('Starting service: {} [count={}]'.format(service, count))

    try:
        response = ecs_client.update_service(
            cluster=cluster,
            service=service,
            desiredCount=count,
        )
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except ecs_client.exceptions.ServiceNotFoundException:
        raise ClickException("Service not found: '{}'".format(service))
    except ClientError as ex:
        raise ClickException(ex)


def start_services(cluster, services, count, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    for service in services:
        start_service(cluster=cluster, service=service, count=count, region=region, ecs_client=ecs_client)


def is_service_type(service, cluster, type, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)
    return ecs_client.describe_services(services=[service], cluster=cluster)['services'][0]['schedulingStrategy'] == type


def is_service_type_daemon(service, cluster, region, ecs_client=None):
    return is_service_type(service=service, cluster=cluster, type='DAEMON', region=region, ecs_client=ecs_client)


def start_cluster_services(cluster, count, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    services = get_services_names(cluster=cluster, region=region, ecs_client=ecs_client)
    non_daemon_services = [service for service in services if not is_service_type_daemon(
        service=service, cluster=cluster, region=region, ecs_client=ecs_client)]

    start_services(cluster=cluster, services=non_daemon_services, count=count, region=region, ecs_client=ecs_client)


def stop_service(cluster, service, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    LOGGER.info('Stopping service: {}'.format(service))

    try:
        response = ecs_client.update_service(
            cluster=cluster,
            service=service,
            desiredCount=0,
        )
    except ClientError as ex:
        raise ClickException(ex)


def stop_cluster_services(cluster, region):
    ecs_client = _get_ecs_client(region)

    try:
        cluster_services = get_services_arns(cluster=cluster, region=region, ecs_client=ecs_client)
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except ClientError as ex:
        raise ClickException(ex)

    non_daemon_services = [service for service in cluster_services if not is_service_type_daemon(
        service=service, cluster=cluster, region=region, ecs_client=ecs_client)]

    for service in non_daemon_services:
        stop_service(cluster=cluster, service=service, region=region, ecs_client=ecs_client)


def run_task(cluster, task_definition, command, name, region, ecs_client=None, **kwargs):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    args = {
        'cluster': cluster,
        'taskDefinition': task_definition,
        'count': 1,
    }

    if command is not None:
        args['overrides'] = {
            'containerOverrides': [
                {
                    'name': name,
                    'command': [command]
                },
            ],
        }

    for key, value in kwargs.items():
        if key != "environmentFiles" and value is not None:
            args[key] = value

    if kwargs.get('environmentFiles') is not None:
        if 'overrides' in args:
            if 'containerOverrides' in args['overrides']:
                args['overrides']['containerOverrides'][0]['environmentFiles'] = [
                    {
                        'type': 's3',
                        'value': kwargs.get('environmentFiles')
                    }
                ]

        else:
            args['overrides'] = {
                'containerOverrides': [
                    {
                        'name': name,
                        'environmentFiles': [
                            {
                                'type': 's3',
                                'value': kwargs.get('environmentFiles')
                            }
                        ]
                    },
                ],
            }

    try:
        resp = ecs_client.run_task(**args)
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except ClientError as ex:
        raise ClickException(ex)

    return resp['tasks'][0]['taskArn']


def wait_for_task_to_stop(cluster, task, timeout, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)
    waiter = ecs_client.get_waiter('tasks_stopped')

    LOGGER.info("Waiting for task '{}' to stop.".format(task))

    try:
        waiter.wait(
            cluster=cluster,
            tasks=[task],
            WaiterConfig={
                'Delay': 1,
                'MaxAttempts': timeout,
            },
        )
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except (ClientError, WaiterError) as ex:
        raise ClickException(ex)

    LOGGER.info("Task '{}' stopped.".format(task))


def wait_for_tasks_to_stop(cluster, tasks, timeout, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)
    waiter = ecs_client.get_waiter('tasks_stopped')

    LOGGER.info('Waiting for tasks {} to stop.'.format(tasks))

    try:
        waiter.wait(
            cluster=cluster,
            tasks=tasks,
            WaiterConfig={
                'Delay': 1,
                'MaxAttempts': timeout,
            },
        )
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except (ClientError, WaiterError) as ex:
        raise ClickException(ex)

    LOGGER.info('All tasks stopped.')


def wait_for_task_to_start(cluster, task, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)
    waiter = ecs_client.get_waiter('tasks_running')

    LOGGER.info('Waiting for task {} to start.'.format(task))

    try:
        waiter.wait(cluster=cluster, tasks=[task])
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except (ClientError, WaiterError) as ex:
        raise ClickException(ex)


def wait_for_tasks_to_start(cluster, tasks, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)
    waiter = ecs_client.get_waiter('tasks_running')

    LOGGER.info('Waiting for tasks {} to start.'.format(tasks))

    try:
        waiter.wait(cluster=cluster, tasks=tasks)
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except (ClientError, WaiterError) as ex:
        raise ClickException(ex)


def run_service_task(cluster, service, command, success_string, timeout, region, container=None, ecs_client=None, **kwargs):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    container = service if not container else container

    task_definition = get_task_definition_for_service(
        cluster=cluster, service=service, region=region, ecs_client=ecs_client)

    latest_task_definition = task_definition[:task_definition.rfind(':')]
    latest_task_definition_name = latest_task_definition[latest_task_definition.rfind('/') + 1:]

    resp = ecs_client.describe_task_definition(taskDefinition=latest_task_definition)
    container_definitions = resp['taskDefinition']['containerDefinitions']

    container_definition = [d for d in container_definitions if d["name"] == container]

    if len(container_definition) != 1:
        raise ClickException(
            ('Container "{}" not found in task.\n'
             'Containers available in task: {}'.format(container, [d["name"] for d in container_definitions])))

    container_name = container_definition[0]['name']

    run_task_and_wait_for_success(
        cluster=cluster,
        task_definition=latest_task_definition_name,
        command=command,
        name=container_name,
        success_string=success_string,
        timeout=timeout,
        region=region,
        ecs_client=ecs_client,
        **kwargs,
    )


def run_task_and_wait_for_success(cluster, task_definition, command, name, success_string, timeout, region, ecs_client=None, **kwargs):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    try:
        task = run_task(
            cluster=cluster,
            task_definition=task_definition,
            command=command,
            name=name,
            region=region,
            ecs_client=ecs_client,
            **kwargs,
        )
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except ClientError as ex:
        raise ClickException(ex)

    task_id = task.split('/')[-1]

    LOGGER.info("Running task: '{}'".format(task))
    wait_for_task_to_stop(cluster=cluster, task=task, timeout=timeout, region=region, ecs_client=ecs_client)
    response = ecs_client.describe_tasks(cluster=cluster, tasks=[task])

    UNDEFINED = 'UNDEFINED'

    task_stop_code = response['tasks'][0].get('stopCode', UNDEFINED)
    LOGGER.info("Task stop code: '{}'".format(task_stop_code))

    container_response = {}
    for _container_response in response['tasks'][0]['containers']:
        if _container_response['name'] == name:
            container_response = _container_response

    if task_stop_code != 'EssentialContainerExited':
        contianer_stop_reason = container_response.get('reason', UNDEFINED)
        LOGGER.info("Container stop reason: '{}'".format(contianer_stop_reason))

        if contianer_stop_reason != UNDEFINED:
            raise ClickException(contianer_stop_reason)

        task_stop_reason = response['tasks'][0].get('stoppedReason', UNDEFINED)
        LOGGER.info("Task stop reason: '{}'".format(task_stop_reason))
        if task_stop_reason != UNDEFINED:
            raise ClickException(task_stop_reason)

        raise ClickException(response['tasks'][0])

    try:
        LOGGER.info('Task output:')
        for event in get_log_events(log_group=task_definition, log_stream='ecs/{}/{}'.format(name, task_id),
                                    region=region):
            LOGGER.info(
                2 * ' ' + '[task/{} - {}] {}'.format(
                    task_id,
                    datetime.fromtimestamp(event['timestamp'] // 1000),
                    event['message'].rstrip()
                )
            )
    except Exception as ex:
        LOGGER.info(ex)

    exit_code = container_response.get('exitCode', UNDEFINED)
    LOGGER.info("Container exit code: '{}'".format(exit_code))

    if exit_code == UNDEFINED:
        raise ClickException("Container exit code: '{}'".format(exit_code))

    if str(exit_code) != success_string:
        raise ClickException(
            "Container exit code is not equal to success_string: '{}' (expected: '{}')".format(
                exit_code,
                success_string,
            )
        )
    LOGGER.info('Success')


def get_services_arns(cluster, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    try:
        resp = ecs_client.list_services(cluster=cluster, maxResults=100)
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except ClientError as ex:
        raise ClickException(ex)

    if 'nextToken' in resp:
        raise ClickException('Getting ARNs of more than 100 cluster services is not implemented')

    services_arns = resp['serviceArns']
    return services_arns


def get_services_names(cluster, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    services_arns = get_services_arns(cluster, region, ecs_client=ecs_client)
    services_names = [service.split('/')[-1] for service in services_arns]
    return services_names


def get_tasks_for_service(cluster, service, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    try:
        resp = ecs_client.list_tasks(cluster=cluster, serviceName=service)
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except ecs_client.exceptions.ServiceNotFoundException:
        raise ClickException("Service not found: '{}'".format(service))
    except ClientError as ex:
        raise ClickException(ex)

    tasks_arns = resp['taskArns']
    return tasks_arns


def stop_services_and_wait_for_tasks_to_stop(cluster, services, timeout, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    THREAD_MAX = 32
    number_of_services = len(services)

    all_running_service_tasks = []

    for service in services:
        running_service_tasks = get_tasks_for_service(
            cluster=cluster,
            service=service,
            region=region,
            ecs_client=ecs_client,
        )

        if running_service_tasks:
            all_running_service_tasks += running_service_tasks
            stop_service(cluster=cluster, service=service, region=region, ecs_client=ecs_client)
        else:
            LOGGER.info("No active tasks found in service '{}'".format(service))

    if all_running_service_tasks:
        pool = ThreadPool(number_of_services if number_of_services < THREAD_MAX else THREAD_MAX)
        pool.starmap(wait_for_task_to_stop, ((cluster, task, timeout, region, ecs_client)
                                             for task in all_running_service_tasks))
        pool.close()
        pool.join()


def stop_service_and_wait_for_tasks_to_stop(cluster, service, timeout, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    tasks = get_tasks_for_service(cluster=cluster, service=service, region=region, ecs_client=ecs_client)

    stop_service(cluster=cluster, service=service, region=region, ecs_client=ecs_client)

    if not tasks:
        LOGGER.info("No active tasks found in service '{}'".format(service))
        return

    wait_for_tasks_to_stop(cluster=cluster, tasks=tasks, timeout=timeout, region=region, ecs_client=ecs_client)


def start_service_and_wait_for_tasks_to_start(cluster, service, count, region, ecs_client=None):
    """ This function is currently not working as the tasks are not started
    immediately after the update of desired count
    """
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    start_service(cluster=cluster, service=service, count=count, region=region, ecs_client=ecs_client)

    tasks = get_tasks_for_service(cluster=cluster, service=service, region=region, ecs_client=ecs_client)
    wait_for_tasks_to_start(cluster=cluster, tasks=tasks, region=region)


def get_min_capacity_for_service(cluster, service, region, as_client=None):
    as_client = as_client if as_client else _get_autoscaling_client(region)

    try:
        response = as_client.describe_scalable_targets(
            ServiceNamespace='ecs',
            ResourceIds=[
                'service/{}/{}'.format(cluster, service),
            ],
        )
    except ecs_client.exceptions.ServiceNotFoundException:
        raise ClickException("Service not found: '{}'".format(service))
    except ClientError as ex:
        raise ClickException(ex)

    targets = response['ScalableTargets']

    if len(targets) < 1:
        raise ClickException(
            "No scalable targets found for cluster '{}' and service name '{}'".format(
                cluster,
                service,
            )
        )
    elif len(targets) > 1:
        raise ClickException(
            'Exactly one service per cluster is supported. Services found: {}'.format(
                len(targets)
            )
        )

    return int(targets[0].get('MinCapacity'))


def redeploy_service(cluster, service, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    LOGGER.info('Redeploying service: {}'.format(service))

    try:
        response = ecs_client.update_service(
            cluster=cluster,
            service=service,
            forceNewDeployment=True,
        )
    except ecs_client.exceptions.ClusterNotFoundException:
        raise ClickException("Cluster not found: '{}'".format(cluster))
    except ecs_client.exceptions.ServiceNotFoundException:
        raise ClickException("Service not found: '{}'".format(service))
    except ClientError as ex:
        raise ClickException(ex)


def redeploy_services(cluster, services, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    for service in services:
        redeploy_service(cluster=cluster, service=service, region=region, ecs_client=ecs_client)


def _get_non_daemon_services(cluster, region, ecs_client):
    services = get_services_names(cluster=cluster, region=region, ecs_client=ecs_client)
    return [
        service for service in services
        if not is_service_type_daemon(service=service, cluster=cluster, region=region, ecs_client=ecs_client)
    ]


def redeploy_cluster_services(cluster, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)

    redeploy_services(cluster=cluster, services=_get_non_daemon_services(cluster, region, ecs_client), region=region,
                      ecs_client=ecs_client)


def wait_for_services_stable(cluster, region, ecs_client=None):
    ecs_client = ecs_client if ecs_client else _get_ecs_client(region)
    waiter = ecs_client.get_waiter('services_stable')

    non_daemon_services = _get_non_daemon_services(cluster, region, ecs_client)

    try:
        for i in range(0, len(non_daemon_services), 10):  # split into chunks by 10
            waiter.wait(cluster=cluster, services=non_daemon_services[i:i + 10])
    except WaiterError as ex:
        raise ClickException(ex)


def run_fargate_debug(cluster, region, task_definition, network_configuration_ssm_parameter, ecs_client=None, ssm_client=None):
    ecs_client= ecs_client if ecs_client else _get_ecs_client(region)
    ssm_client= ssm_client if ssm_client else _get_ssm_client(region)

    # Get network configuration from SSM
    try:
        LOGGER.info('Getting network configuration from SSM parameter')
        resp = ssm_client.get_parameter(Name=network_configuration_ssm_parameter, WithDecryption=True)
    except ClientError as ex:
        raise ClickException(f"{ex.response['Error']['Code']}: {ex.response['Error']['Message']}")
    network_configuration = resp['Parameter']['Value']

    try:
        LOGGER.info('Running Fargate ECS task')
        resp = ecs_client.run_task(
            launchType='FARGATE',
            enableExecuteCommand=True,
            cluster=cluster,
            taskDefinition=task_definition,
            networkConfiguration=json.loads(network_configuration),
            propagateTags='TASK_DEFINITION',
        )
    except ClientError as ex:
        raise ClickException(f"{ex.response['Error']['Code']}: {ex.response['Error']['Message']}")
    task_arn = resp['tasks'][0]['taskArn']
    LOGGER.info('Task "%s" started', task_arn)

    waiter = ecs_client.get_waiter('tasks_running')
    LOGGER.info('Waiting for the task to become ready')
    waiter.wait(cluster=cluster, tasks=[task_arn])
    LOGGER.info('Task is ready!')

    LOGGER.info('We have to sleep for a bit before the SSM agent becomes ready... sleeping for 15 seconds')
    time.sleep(15)
    LOGGER.info('I am awake!')

    LOGGER.info('Running ECS Execute Command')
    call_command(f'aws ecs execute-command --color on --cli-connect-timeout 15 --cli-read-timeout 15 --cluster {cluster} --interactive --command sh --task {task_arn}')
    LOGGER.info('I solemnly swear that I am up to no good.')
