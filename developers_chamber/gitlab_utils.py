from urllib.parse import quote_plus

import requests
from click import UsageError


def create_merge_request(api_url, token, title, description, source_branch, target_branch, project):
    # TODO: Add support for assigning these MRs to the person who started deploy
    response = requests.post(
        f'{api_url}/projects/{quote_plus(project)}/merge_requests',
        headers={
            'PRIVATE-TOKEN': token,
        },
        json={
            'source_branch': source_branch,
            'target_branch': target_branch,
            'title': title,
            'description': description,
        },
    )

    if response.status_code != 201:
        raise UsageError(f'GitLab error: {response.content.decode("utf-8")}')
    return response.json()['web_url']
