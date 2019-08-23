import requests

from requests.auth import HTTPBasicAuth

from click import UsageError


def create_merge_release_pull_request(username, password, source_branch_name, destination_branch_name, repository_name):
    url = 'https://api.bitbucket.org/2.0/repositories/{repository}/pullrequests'.format(
        repository=repository_name
    )
    headers = {'content-type': 'application/json'}

    json_data = {
        'title': 'Merge branch "{}"'.format(source_branch_name),
        'source': {
            'branch': {
                'name': source_branch_name
            }
        },
        'destination': {
            'branch': {
                'name': destination_branch_name
            }
        }
    }
    resp = requests.post(url, headers=headers, json=json_data, auth=HTTPBasicAuth(username, password))
    if resp.status_code != 201:
        raise UsageError('Bitbucket error: {}'.format(resp.content.decode('utf-8')))
    return resp.json()['links']['html']['href']