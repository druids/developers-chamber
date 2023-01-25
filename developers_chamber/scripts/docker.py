import click

from developers_chamber.click.options import RequiredIfNotEmpty
from developers_chamber.docker_utils import login_client as login_client_func
from developers_chamber.docker_utils import push_image as push_image_func
from developers_chamber.docker_utils import tag as tag_func
from developers_chamber.scripts import cli


@cli.group()
def docker():
    """Docker utilities helping with managing docker in your project."""
    pass


@docker.command()
@click.option('--username', '-u', help='registry username', type=str, cls=RequiredIfNotEmpty,
              required_if_empty='password')
@click.option('--password', '-p', help='registry password', type=str, cls=RequiredIfNotEmpty,
              required_if_empty='username')
@click.option('-r', '--registry', help='registry url', type=str, default='hub.docker.com')
def login(username, password, registry):
    """
    Login to the docker registry.
    """
    click.echo(login_client_func(username, password, registry))


@docker.command()
@click.option('--source-image', '-s', help='source image including tag', type=str, required=True)
@click.option('--target-image', '-t', help='target image including tag', type=str, required=True)
def tag(source_image, target_image):
    """
    Tag a docker image.
    """
    click.echo(tag_func(source_image, target_image))


@docker.command()
@click.option('--repository', '-r', help='repository', type=str, required=True)
@click.option('--tag', '-t', help='image tag', type=str, default='latest')
def push_image(repository, tag):
    """
    Push image to the docker repository.
    """
    click.echo(push_image_func(repository, tag))
