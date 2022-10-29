import requests
from click import UsageError
from requests.auth import HTTPBasicAuth


def get_commit_builds(username, password, repository_name, commit):
    response = requests.get(
        'https://api.bitbucket.org/2.0/repositories/{repository}/commit/{commit}/statuses'.format(
            repository=repository_name, commit=commit
        ), headers={'content-type': 'application/json'},
        auth=HTTPBasicAuth(username, password)
    )
    if response.status_code != 200:
        raise UsageError('Bitbucket error: {}'.format(response.content.decode('utf-8')))
    return [
        build_data
        for build_data in response.json()['values']
        if build_data['type'] == 'build'
    ]


def get_current_user_uuid(username, password):
    response = requests.get(
        'https://api.bitbucket.org/2.0/user', headers={'content-type': 'application/json'},
        auth=HTTPBasicAuth(username, password)
    )
    if response.status_code != 200:
        raise UsageError('Bitbucket error: {}'.format(response.content.decode('utf-8')))
    return response.json()['uuid']


def get_default_reviewers(username, password, repository_name):
    url = 'https://api.bitbucket.org/2.0/repositories/{repository}/default-reviewers'.format(
        repository=repository_name
    )
    response = requests.get(url, headers={'content-type': 'application/json'}, auth=HTTPBasicAuth(username, password))
    if response.status_code != 200:
        raise UsageError('Bitbucket error: {}'.format(response.content.decode('utf-8')))
    current_user_uuid = get_current_user_uuid(username, password)
    return [
        {'uuid': reviewer_data['uuid']} for reviewer_data in response.json()['values']
        if reviewer_data['uuid'] != current_user_uuid
    ]


def create_pull_request(username, password, title, description, source_branch_name, destination_branch_name,
                        repository_name):
    url = 'https://api.bitbucket.org/2.0/repositories/{repository}/pullrequests'.format(
        repository=repository_name
    )
    json_data = {
        'title': title,
        'description': description,
        'source': {
            'branch': {
                'name': source_branch_name
            }
        },
        'destination': {
            'branch': {
                'name': destination_branch_name
            }
        },
        'reviewers': get_default_reviewers(username, password, repository_name),
    }
    response = requests.post(
        url, headers={'content-type': 'application/json'}, json=json_data, auth=HTTPBasicAuth(username, password)
    )
    if response.status_code != 201:
        raise UsageError('Bitbucket error: {}'.format(response.content.decode('utf-8')))
    return response.json()['links']['html']['href']


def create_merge_release_pull_request(username, password, source_branch_name, destination_branch_name, repository_name):
    return create_pull_request(
        username=username,
        password=password,
        title='Merge branch "{}"'.format(source_branch_name),
        description='',
        source_branch_name=source_branch_name,
        destination_branch_name=destination_branch_name,
        repository_name=repository_name
    )
