from jira import JIRA

import unicodedata

from .git import create_branch


def remove_accent(string_with_diacritics):
    """
    Removes a diacritics from a given string"
    """
    return unicodedata.normalize('NFKD', string_with_diacritics).encode('ASCII', 'ignore').decode('ASCII')


def create_branch_from_jira_task(jira_url, jira_username, jira_password, jira_issue_id, source_branch, remote_name):
    jira = JIRA(jira_url, auth_basic=(jira_username, jira_password))
    issue = jira.issue(jira_issue_id)

    branch_name = '{}-{}'.format(jira_issue_id, remove_accent(issue.fields.summary).replace(' ', '-'))
    create_branch(source_branch, branch_name, remote_name)


def create_pull_request(jira_url, jira_username, jira_password, remote_name):
    ...
