import os

import click

from developers_chamber.jira_utils import \
    get_branch_name as get_branch_name_func
from developers_chamber.jira_utils import (get_current_user_issues,
                                           get_issue_worklog)
from developers_chamber.jira_utils import \
    invoke_issues_transition as invoke_issues_transition_func
from developers_chamber.jira_utils import log_issue_time as log_issue_time_func
from developers_chamber.jira_utils import show_issue as show_issue_func
from developers_chamber.scripts import cli
from developers_chamber.types import TimedeltaType

url = os.environ.get('JIRA_URL')
username = os.environ.get('JIRA_USERNAME')
api_key = os.environ.get('JIRA_API_KEY')
jql = os.environ.get(
    'JIRA_JQL',
    'project = {project_key} and assignee = currentUser() and status not in ("Done", "Canceled", "Closed") and sprint !'
    '= null order by created DESC'
)
project_key = os.environ.get('JIRA_PROJECT_KEY')


@cli.group()
def jira():
    """Helpers for Jira management."""


@jira.command()
@click.option('--url', '-u',  help='Jira URL', type=str, required=True, default=url)
@click.option('--username', '-a',  help='Jira username', type=str, required=True, default=username)
@click.option('--api-key', '-p',  help='Jira API key/password', type=str, required=True, default=api_key)
@click.option('--project-key',  help='Jira project key', type=str, required=False, default=project_key)
@click.option('--jql',  help='JQL', type=str, required=True, default=jql)
def my_issues(url, username, api_key, project_key, jql):
    """
    List open Jira tasks for the current user.
    """
    click.echo(get_current_user_issues(url, username, api_key, project_key, jql))


@jira.command()
@click.option('--url', '-u',  help='Jira URL', type=str, required=True, default=url)
@click.option('--username', '-a',  help='Jira username', type=str, required=True, default=username)
@click.option('--api-key', '-p',  help='Jira API key/password', type=str, required=True, default=api_key)
@click.option('--project-key',  help='Jira project key', type=str, required=False, default=project_key)
@click.option('--issue-key', '-i',  help='key of the task', type=str, required=True)
def get_branch_name(url, username, api_key, project_key, issue_key):
    """
    Return branch name generated from issue key and summary.
    """
    click.echo(get_branch_name_func(url, username, api_key, issue_key, project_key))


@jira.command()
@click.option('--url', '-u',  help='Jira URL', type=str, required=True, default=url)
@click.option('--username', '-a',  help='Jira username', type=str, required=True, default=username)
@click.option('--api-key', '-p',  help='Jira API key/password', type=str, required=True, default=api_key)
@click.option('--project-key',  help='Jira project key', type=str, required=False, default=project_key)
@click.option('--issue-key', '-i',  help='key of the task', type=str)
def show_issue(url, username, api_key, project_key, issue_key):
    """
    Open an issue with the key in a web browser.
    """
    show_issue_func(url, username, api_key, issue_key, project_key)


@jira.command()
@click.option('--url', '-u',  help='Jira URL', type=str, required=True, default=url)
@click.option('--username', '-a',  help='Jira username', type=str, required=True, default=username)
@click.option('--api-key', '-p',  help='Jira API key/password', type=str, required=True, default=api_key)
@click.option('--project-key',  help='Jira project key', type=str, required=False, default=project_key)
@click.option('--issue-key', '-i',  help='key of the task', type=str)
@click.option('--time-spend', '-t',  help='Time spend (ex. 1d, 1h, etc.)', type=TimedeltaType(), required=True)
@click.option('--comment', '-c',  help='Time spend comment', type=str, required=False)
def log_issue_time(url, username, api_key, project_key, issue_key, time_spend, comment):
    """
    Log a spend time to the issue in Jira.
    """
    log_issue_time_func(url, username, api_key, issue_key, time_spend, comment, project_key)
    click.echo('Time was logged')


@jira.command()
@click.option('--url', '-u',  help='Jira URL', type=str, required=True, default=url)
@click.option('--username', '-a',  help='Jira username', type=str, required=True, default=username)
@click.option('--api-key', '-p',  help='Jira API key/password', type=str, required=True, default=api_key)
@click.option('--project-key',  help='Jira project key', type=str, required=False, default=project_key)
@click.option('--issue-key', '-i',  help='key of the task', type=str)
def print_issue_worklog(url, username, api_key, project_key, issue_key):
    """
    Print an issue worklog from Jira.
    """
    click.echo('{:<15} | {}'.format('Time', 'Description'))
    click.echo(16 * '-' + '+' + 16 * '-')
    for worklog in get_issue_worklog(url, username, api_key, issue_key, project_key):
        click.echo('{:<15} | {}'.format(worklog.timeSpent, worklog.comment))


@jira.command()
@click.option('--url', '-u',  help='Jira URL', type=str, required=True, default=url)
@click.option('--username', '-a',  help='Jira username', type=str, required=True, default=username)
@click.option('--api-key', '-p',  help='Jira API key/password', type=str, required=True, default=api_key)
@click.option('--jql',  help='JQL', type=str, required=True)
@click.option('--transition',  help='Jira transition name', type=str, required=True)
def invoke_issues_transition(url, username, api_key, jql, transition):
    """
    Apply transition on selected issues in Jira according to JQL.
    """
    issues = invoke_issues_transition_func(url, username, api_key, jql, transition)
    click.echo(
        'Transition "{}" was invoked on issues "{}"'.format(transition, ', '.join(str(issue) for issue in issues))
    )
