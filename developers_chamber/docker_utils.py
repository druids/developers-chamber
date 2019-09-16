import docker

import click


client = docker.from_env()


def login_client(username, password, registry):
    try:
        client.login(username=username, password=password, registry=registry)
    except docker.errors.APIError as ex:
        raise click.UsageError('Login to registry "{}" failed with following message: {}'.format(registry,
                                                                                                 ex.explanation))

def tag(source_image, target_image):
    try:
        image = client.images.get(source_image)
    except docker.errors.ImageNotFound:
        raise click.UsageError('Image "{}" does not exist'.format(source_image))
    except docker.errors.APIError as ex:
        raise click.UsageError('Communication with registry failed with following message: {}'.format(ex.explanation))
    image.tag(target_image)


def push_image(repository, tag):
    try:
        response = client.images.push(repository, tag, stream=True, decode=True)
    except docker.errors.APIError as ex:
        raise click.UsageError(
            'Pushing image to repository "{}" failed with following message: {}'.format(repository, ex.explanation)
        )

    for line in response:
        click.echo(line)
