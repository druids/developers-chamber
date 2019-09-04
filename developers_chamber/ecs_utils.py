import logging

import boto3
from botocore.client import Config

LOGGER = logging.getLogger()


def _get_ecs_client(region):
    return boto3.client(
        'ecs',
        config=Config(region_name=region),
    )


def deploy_new_task_definition(cluster, service, task_definition, image, region):
    ecs_client = _get_ecs_client(region)
    old_task = ecs_client.describe_task_definition(
        taskDefinition=task_definition,
        include=[
            'TAGS',
        ]
    )

    LOGGER.info('Image: {}'.format(image))
    LOGGER.info('Old task definition:\n{}'.format(old_task))

    definition = old_task['taskDefinition']
    definition['containerDefinitions'][0]['image'] = image
    new_definition = {
        'family': definition['family'],
        'taskRoleArn': definition['taskRoleArn'],
        'executionRoleArn': definition['executionRoleArn'],
        'networkMode': definition['networkMode'],
        'containerDefinitions': definition['containerDefinitions'],
        'requiresCompatibilities': definition['requiresCompatibilities'],
        'tags': old_task['tags'],
    }

    if 'cpu' in definition:
        new_definition['cpu'] = definition['cpu']
    if 'memory' in definition:
        new_definition['memory'] = definition['memory']

    new_task = ecs_client.register_task_definition(**new_definition)
    revision = new_task['taskDefinition']['revision']
    ecs_client.update_service(
        cluster=cluster,
        service=service,
        taskDefinition='{}:{}'.format(task_definition, revision),
        forceNewDeployment=True,
    )


def stop_service(cluster, service, region):
    ecs_client = _get_ecs_client(region)
    response = ecs_client.update_service(
        cluster=cluster,
        service=service,
        desiredCount=0,
    )

    LOGGER.info('Service response:\n{}'.format(response))


def run_task(cluster, task_definition, command, name, region):
    ecs_client = _get_ecs_client(region)
    response = ecs_client.run_task(
        cluster=cluster,
        taskDefinition=task_definition,
        overrides={
            'containerOverrides': [
                {
                    'name': name,
                    'command': command.split(' '),
                },
            ],
        },
        count=1,
    )

    return response
