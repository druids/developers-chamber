import click

from developers_chamber.click.options import RequiredIfNotEmpty
from developers_chamber.docker_utils import login_client as login_client_func
from developers_chamber.docker_utils import push_image as push_image_func
from developers_chamber.docker_utils import tag as tag_func
from developers_chamber.scripts import cli


@cli.group()
def docker():
    """Docker utilities."""
    pass


@docker.command()
@click.option('-u', '--username', help='registry username', type=str, cls=RequiredIfNotEmpty,
              required_if_empty='password')
@click.option('-p', '--password', help='registry password', type=str, cls=RequiredIfNotEmpty,
              required_if_empty='username')
@click.option('-r', '--registry', help='registry url', type=str, default='hub.docker.com')
def login(username, password, registry):
    click.echo(login_client_func(username, password, registry))


@docker.command()
@click.option('-s', '--source-image', help='source image including tag', type=str, required=True)
@click.option('-t', '--target-image', help='target image including tag', type=str, required=True)
def tag(source_image, target_image):
    click.echo(tag_func(source_image, target_image))


@docker.command()
@click.option('-r', '--repository', help='repository', type=str, required=True)
@click.option('-t', '--tag', help='image tag', type=str, default='latest')
def push_image(repository, tag):
    click.echo(push_image_func(repository, tag))
