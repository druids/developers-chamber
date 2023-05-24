import os

import click

from developers_chamber.scripts import cli
from developers_chamber.slack_utils import \
    upload_new_migration as upload_new_migration_func
from developers_chamber.utils import MIGRATIONS_PATTERN

slack_bot_token = os.environ.get('SLACK_BOT_TOKEN')
TARGET_BRANCH = 'master'


@cli.group()
def slack():
    """Helpers for Slack management."""


@slack.command()
@click.option('--token', help='Slack bot token',
              type=str, required=True, default=slack_bot_token)
@click.option('--channel', help='Channel name where to send migration files',
              type=str, required=True)
@click.option('--target-branch', help='Name of the branch to compare',
              type=str, required=True, default=TARGET_BRANCH)
@click.option('--migrations-pattern', help='Regex pattern to match migration files',
              type=str, required=True, default=MIGRATIONS_PATTERN)
def upload_new_migrations(token, channel, target_branch, migrations_pattern):
    """
    Send all new Django migration files between releases etc. to Slack
    """
    upload_new_migration_func(token, channel, target_branch, migrations_pattern)
    click.echo('Done')
