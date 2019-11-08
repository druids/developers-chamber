import logging
from multiprocessing.pool import ThreadPool

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, WaiterError
from click import ClickException

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


def get_log_events(log_group, log_stream, region):
    logs_client = _get_logs_client(region)

    try:
        resp = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            limit=10000,
        )
    except ClientError as ex:
        raise ClickException(ex)

    return resp['events']


def register_new_task_definition(task_definition, image, region):
    ecs_client = _get_ecs_client(region)

    try:
        old_task_definition = ecs_client.describe_task_definition(
            taskDefinition=task_definition,
            include=[
                'TAGS',
            ],
        )
    except ClientError as ex:
        raise ClickException(ex)

    LOGGER.info('Image: {}'.format(image))
    LOGGER.info('Old task definition ARN: {}'.format(
        old_task_definition['taskDefinition']['taskDefinitionArn']),
    )

    definition = old_task_definition['taskDefinition']
    definition['containerDefinitions'][0]['image'] = image
    new_task_definition = {
        'family': definition['family'],
        'taskRoleArn': definition['taskRoleArn'],
        'executionRoleArn': definition['executionRoleArn'],
        'networkMode': definition['networkMode'],
        'containerDefinitions': definition['containerDefinitions'],
        'requiresCompatibilities': definition['requiresCompatibilities'],
        'tags': old_task_definition['tags'],
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
    LOGGER.info('New task definition ARN: {}'.format(new_task_definition_arn))

    return new_task_definition_arn


def get_task_definition_for_service(cluster, service, region):
    ecs_client = _get_ecs_client(region)

    services = ecs_client.describe_services(
        cluster=cluster,
        services=[service],
    )

    number_of_services = len(services['services'])

    if number_of_services > 1:
        raise ClickException(
            'More than one service with the same name found: {}'.format(
                len(services['services']),
            )
        )
    elif number_of_services == 0:
        raise ClickException(
            'No services with the name \'{}\' found.'.format(service)
        )

    return services['services'][0]['taskDefinition']


def update_service_to_latest_task_definition(cluster, service, region):
    ecs_client = _get_ecs_client(region)

    old_task_definition = get_task_definition_for_service(cluster=cluster, service=service, region=region)
    LOGGER.info('Current task definition ARN: {}'.format(old_task_definition))

    new_task_definition = ecs_client.describe_task_definition(
        taskDefinition=old_task_definition[:old_task_definition.rfind(':')]
    )
    new_task_definition_arn = new_task_definition['taskDefinition']['taskDefinitionArn']
    LOGGER.info('New task definition ARN: {}'.format(new_task_definition_arn))

    update_service_to_new_task_definition(
        cluster=cluster,
        service=service,
        task_definition=new_task_definition_arn,
        region=region,
    )


def update_service_to_new_task_definition(cluster, service, task_definition, region):
    ecs_client = _get_ecs_client(region)

    try:
        response = ecs_client.update_service(
            cluster=cluster,
            service=service,
            taskDefinition=task_definition,
            forceNewDeployment=True,
        )
    except ClientError as ex:
        raise ClickException(ex)


def deploy_new_task_definition(cluster, service, task_definition, image, region):
    ecs_client = _get_ecs_client(region)

    new_task_definition = register_new_task_definition(task_definition=task_definition, image=image, region=region)

    update_service_to_new_task_definition(
        cluster=cluster,
        service=service,
        task_definition=new_task_definition,
        region=region,
    )


def start_service(cluster, service, count, region):
    if count is None:
        try:
            count = get_min_capacity_for_service(cluster=cluster, service=service, region=region)
        except ClickException as ex:
            raise ClickException(
                'Set explicit count or set up autoscaling with minimum capacity.\n{}'.format(ex)
            )

    ecs_client = _get_ecs_client(region)

    LOGGER.info('Starting service: {} [count={}]'.format(service, count))

    try:
        response = ecs_client.update_service(
            cluster=cluster,
            service=service,
            desiredCount=count,
        )
    except ClientError as ex:
        raise ClickException(ex)


def start_services(cluster, count, region):
    ecs_client = _get_ecs_client(region)

    services = get_services_arns(cluster=cluster, region=region)

    if count is not None and count < 1:
        raise ClickException('Count must be greater than zero or \'None\' to be determined from autoscaling targets.')

    for service in services:
        count_per_service = count
        service_name = service.split('/')[1]
        if count_per_service is None:
            try:
                count_per_service = get_min_capacity_for_service(cluster=cluster, service=service_name, region=region)
            except ClickException as ex:
                raise ClickException(
                    'Set explicit count or set up autoscaling with minimum capacity.\n{}'.format(ex)
                )

        LOGGER.info('Starting service: {}'.format(service))
        try:
            ecs_client.update_service(
                cluster=cluster,
                service=service,
                desiredCount=count_per_service,
            )
        except ClientError as ex:
            raise ClickException(ex)


def stop_service(cluster, service, region):
    ecs_client = _get_ecs_client(region)

    LOGGER.info('Stopping service: {}'.format(service))

    try:
        response = ecs_client.update_service(
            cluster=cluster,
            service=service,
            desiredCount=0,
        )
    except ClientError as ex:
        raise ClickException(ex)


def stop_services(cluster, region):
    ecs_client = _get_ecs_client(region)

    try:
        services = get_services_arns(cluster=cluster, region=region)
    except ClientError as ex:
        raise ClickException(ex)

    for service in services:
        try:
            LOGGER.info('Stopping service: {}'.format(service))
            ecs_client.update_service(
                cluster=cluster,
                service=service,
                desiredCount=0,
            )
        except ClientError as ex:
            raise ClickException(ex)


def run_task(cluster, task_definition, command, name, region):
    ecs_client = _get_ecs_client(region)

    if command is None:
        try:
            resp = ecs_client.run_task(
                cluster=cluster,
                taskDefinition=task_definition,
                count=1,
            )
        except ClientError as ex:
            raise ClickException(ex)
    else:
        try:
            resp = ecs_client.run_task(
                cluster=cluster,
                taskDefinition=task_definition,
                overrides={
                    'containerOverrides': [
                        {
                            'name': name,
                            'command': [command]
                        },
                    ],
                },
                count=1,
            )
        except ClientError as ex:
            raise ClickException(ex)

    return resp['tasks'][0]['taskArn']


def wait_for_task_to_stop(cluster, task, timeout, region):
    ecs_client = _get_ecs_client(region)
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
    except (ClientError, WaiterError) as ex:
        raise ClickException(ex)

    LOGGER.info("Task '{}' stopped.".format(task))


def wait_for_tasks_to_stop(cluster, tasks, timeout, region):
    ecs_client = _get_ecs_client(region)
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
    except (ClientError, WaiterError) as ex:
        raise ClickException(ex)

    LOGGER.info('All tasks stopped.')


def wait_for_task_to_start(cluster, task, region):
    ecs_client = _get_ecs_client(region)
    waiter = ecs_client.get_waiter('tasks_running')

    LOGGER.info('Waiting for task {} to start.'.format(task))

    try:
        waiter.wait(cluster=cluster, tasks=[task])
    except (ClientError, WaiterError) as ex:
        raise ClickException(ex)


def wait_for_tasks_to_start(cluster, tasks, region):
    ecs_client = _get_ecs_client(region)
    waiter = ecs_client.get_waiter('tasks_running')

    LOGGER.info('Waiting for tasks {} to start.'.format(tasks))

    try:
        waiter.wait(cluster=cluster, tasks=tasks)
    except (ClientError, WaiterError) as ex:
        raise ClickException(ex)


def migrate_service(cluster, service, command, success_string, timeout, region):
    ecs_client = _get_ecs_client(region)

    task_definition = get_task_definition_for_service(cluster=cluster, service=service, region=region)

    latest_task_definition = task_definition[:task_definition.rfind(':')]
    latest_task_definition_name = latest_task_definition[latest_task_definition.rfind('/') + 1:]

    resp = ecs_client.describe_task_definition(taskDefinition=latest_task_definition)
    container_definitions = resp['taskDefinition']['containerDefinitions']

    if len(container_definitions) != 1:
        raise ClickException(
            ('Exactly one container is allowed to be specified in service.\n'
             'Number of containers specified: {}'.format(len(container_definitions)))
        )

    container_name = container_definitions[0]['name']

    run_task_and_wait_for_success(
        cluster=cluster,
        task_definition=latest_task_definition_name,
        command=command,
        name=container_name,
        success_string=success_string,
        timeout=timeout,
        region=region,
    )


def run_task_and_wait_for_success(cluster, task_definition, command, name, success_string, timeout, region):
    ecs_client = _get_ecs_client(region)
    task = run_task(
        cluster=cluster,
        task_definition=task_definition,
        command=command,
        name=name,
        region=region,
    )
    task_id = task.split('/')[1]

    LOGGER.info('Running task: \'{}\''.format(task))

    wait_for_task_to_stop(cluster=cluster, task=task, timeout=timeout, region=region)

    response = ecs_client.describe_tasks(cluster=cluster, tasks=[task])

    UNDEFINED = 'UNDEFINED'

    task_stop_code = response['tasks'][0].get('stopCode', UNDEFINED)
    LOGGER.info('Task stop code: \'{}\''.format(task_stop_code))

    if task_stop_code != 'EssentialContainerExited':
        contianer_stop_reason = response['tasks'][0]['containers'][0].get('reason', UNDEFINED)
        LOGGER.info('Container stop reason: \'{}\''.format(contianer_stop_reason))

        if contianer_stop_reason != UNDEFINED:
            raise ClickException(contianer_stop_reason)

        task_stop_reason = response['tasks'][0].get('stoppedReason', UNDEFINED)
        LOGGER.info('Task stop reason: \'{}\''.format(task_stop_reason))

        if task_stop_reason != UNDEFINED:
            raise ClickException(task_stop_reason)

        raise ClickException(response['tasks'][0])

    for event in get_log_events(log_group=task_definition, log_stream='ecs/{}/{}'.format(name, task_id),
                                region=region):
        LOGGER.info('[task/{}] {}'.format(task_id, event['message'].rstrip()))

    exit_code = response['tasks'][0]['containers'][0].get('exitCode', UNDEFINED)
    LOGGER.info('Container exit code: \'{}\''.format(exit_code))

    if exit_code == UNDEFINED:
        raise ClickException('Container exit code: \'{}\''.format(exit_code))

    if str(exit_code) != success_string:
        raise ClickException(
            "Container exit code is not equal to success_string: \'{}\' (expected: \'{}\')".format(
                exit_code,
                success_string,
            )
        )
    LOGGER.info('Success')


def get_services_arns(cluster, region):
    ecs_client = _get_ecs_client(region)
    resp = ecs_client.list_services(cluster=cluster)
    services_arns = resp['serviceArns']
    return services_arns


def get_tasks_for_service(cluster, service, region):
    ecs_client = _get_ecs_client(region)
    resp = ecs_client.list_tasks(cluster=cluster, serviceName=service)
    tasks_arns = resp['taskArns']
    return tasks_arns


def stop_services_and_wait_for_tasks_to_stop(cluster, services, timeout, region):
    ecs_client = _get_ecs_client(region)

    THREAD_MAX = 32
    number_of_services = len(services)

    all_running_service_tasks = []

    for service in services:
        running_service_tasks = get_tasks_for_service(cluster=cluster, service=service, region=region)

        if running_service_tasks:
            all_running_service_tasks += running_service_tasks
            stop_service(cluster=cluster, service=service, region=region)
        else:
            LOGGER.info("No active tasks found in service '{}'".format(service))

    if all_running_service_tasks:
        pool = ThreadPool(number_of_services if number_of_services < THREAD_MAX else THREAD_MAX)
        pool.starmap(wait_for_task_to_stop, ((cluster, task, timeout, region) for task in all_running_service_tasks))
        pool.close()
        pool.join()


def stop_service_and_wait_for_tasks_to_stop(cluster, service, timeout, region):
    ecs_client = _get_ecs_client(region)

    tasks = get_tasks_for_service(cluster=cluster, service=service, region=region)

    stop_service(cluster=cluster, service=service, region=region)

    if not tasks:
        LOGGER.info('No active tasks found in service \'{}\''.format(service))
        return

    wait_for_tasks_to_stop(cluster=cluster, tasks=tasks, timeout=timeout, region=region)


def start_service_and_wait_for_tasks_to_start(cluster, service, count, region):
    """ This function is currently not working as the tasks are not started
    immediately after the update of desired count
    """
    ecs_client = _get_ecs_client(region)

    start_service(cluster=cluster, service=service, count=count, region=region)

    tasks = get_tasks_for_service(cluster=cluster, service=service, region=region)
    wait_for_tasks_to_start(cluster=cluster, tasks=tasks, region=region)


def get_min_capacity_for_service(cluster, service, region):
    as_client = _get_autoscaling_client(region)

    response = as_client.describe_scalable_targets(
        ServiceNamespace='ecs',
        ResourceIds=[
            'service/{}/{}'.format(cluster, service),
        ],
    )
    targets = response['ScalableTargets']

    if len(targets) < 1:
        raise ClickException(
            'No scalable targets found for cluster \'{}\' and service name \'{}\''.format(
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
