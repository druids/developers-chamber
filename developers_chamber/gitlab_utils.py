from urllib.parse import quote_plus

import requests
from click import UsageError


def create_merge_request(api_url, token, title, description, source_branch, target_branch, project, assignee_id):
    data = {
        'source_branch': source_branch,
        'target_branch': target_branch,
        'title': title,
        'description': description,
    }
    if assignee_id:
        data['assignee_id'] = assignee_id

    response = requests.post(
        f'{api_url}/projects/{quote_plus(project)}/merge_requests',
        headers={
            'PRIVATE-TOKEN': token,
        },
        json=data,
    )

    if response.status_code != 201:
        raise UsageError(f'GitLab error: {response.content.decode("utf-8")}')
    return response.json()['web_url']
