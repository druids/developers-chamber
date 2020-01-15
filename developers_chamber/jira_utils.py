import math
import re
import webbrowser

import click
import unidecode
from jira import JIRA, JIRAError
from requests.exceptions import ConnectionError

from .git_utils import get_current_issue_key


def clean_issue_key(issue_key=None, project_key=None):
    if not issue_key:
        issue_key = get_current_issue_key()

    if not issue_key:
        raise click.UsageError('Please set task key')

    if project_key and not issue_key.startswith('{}-'.format(project_key)):
        return '{}-{}'.format(project_key, issue_key)
    else:
        return issue_key


def get_jira_client(url, username, api_key):
    try:
        client = JIRA(url, basic_auth=(username, api_key))
        return client
    except ConnectionError:
        raise click.BadParameter('Invalid Jira URL or connection problem')


def get_current_user_issues(url, username, api_key, project_key, jql):
    issues = get_jira_client(url, username, api_key).search_issues(jql.format(
        project_key=project_key
    ))
    return '\n'.join(
        ['    - {}: {} ({})'.format(issue.key, issue.fields.summary, issue.permalink()) for issue in issues]
    )


def get_branch_name(url, username, api_key, issue_key, project_key=None):
    issue_key = clean_issue_key(issue_key, project_key)

    try:
        issue = get_jira_client(url, username, api_key).issue(issue_key)
        branch_name = unidecode.unidecode(issue.fields.summary).lower()
        branch_name = re.sub('[^a-zA-Z0-9_ ]+', '', branch_name)
        branch_name = re.sub(' +', '-', branch_name)
        return '{}_{}'.format(issue.key, branch_name)[:40]
    except JIRAError:
        raise click.BadParameter('Invalid issue key {}'.format(issue_key))


def show_issue(url, username, api_key, issue_key, project_key=None):
    issue_key = clean_issue_key(issue_key, project_key)

    try:
        issue = get_jira_client(url, username, api_key).issue(issue_key)
        webbrowser.open(issue.permalink())
    except JIRAError:
        raise click.BadParameter('Invalid issue key {}'.format(issue_key))


def get_issue_fields(url, username, api_key, issue_key, project_key=None):
    issue_key = clean_issue_key(issue_key, project_key)
    try:
        issue = get_jira_client(url, username, api_key).issue(issue_key)
        return issue.fields
    except JIRAError:
        raise click.BadParameter('Invalid issue key {}'.format(issue_key))


def log_issue_time(url, username, api_key, issue_key, time_spend, comment=None, project_key=None):
    issue_key = clean_issue_key(issue_key, project_key)

    try:
        jira = get_jira_client(url, username, api_key)
        issue = jira.issue(issue_key)
        jira.add_worklog(
            issue,
            timeSpent='{}m'.format(math.ceil(time_spend.total_seconds()/60)),
            comment=comment
        )
    except JIRAError:
        raise click.BadParameter('Invalid issue key {}'.format(issue_key))


def get_issue_worklog(url, username, api_key, issue_key, project_key=None):
    issue_key = clean_issue_key(issue_key, project_key)

    try:
        jira = get_jira_client(url, username, api_key)
        issue = jira.issue(issue_key)
        return issue.fields.worklog.worklogs
    except JIRAError:
        raise click.BadParameter('Invalid issue key {}'.format(issue_key))


def invoke_issues_transition(url, username, api_key, jql, transition):
    jira = get_jira_client(url, username, api_key)
    issues = jira.search_issues(jql)
    for issue in issues:
        jira.transition_issue(issue, transition=transition)
    return issues
