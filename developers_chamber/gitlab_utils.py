from urllib.parse import quote_plus

import time
import requests
from click import UsageError


def create_merge_request(
    api_url, token, title, description, source_branch, target_branch, project, assignee_id=None, automerge=False
):
    response = requests.post(
        f"{api_url}/projects/{quote_plus(project)}/merge_requests",
        headers={
            "PRIVATE-TOKEN": token,
        },
        json={
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
            "assignee_id": assignee_id
        },
    )

    if response.status_code != 201:
        raise UsageError(f'GitLab error: {response.content.decode("utf-8")}')

    if automerge:
        time.sleep(5)
        message = activate_automerge(api_url, token, project, response.json()['iid'])
        return f"{response.json()['web_url']} ({message})"

    return response.json()['web_url']


def activate_automerge(
    api_url, token, project, merge_request_id
):
    merge_response = requests.put(
        f"{api_url}/projects/{quote_plus(project)}/merge_requests/{merge_request_id}/merge",
        json={"merge_when_pipeline_succeeds": True},
        headers={
            "PRIVATE-TOKEN": token,
        },
    )
    if merge_response.status_code != 200:
        raise "Automerge activation failed"
    else:
        return "Automerge activated"


def run_job(
    api_url, token, project, ref, variables
):
    response = requests.post(
        f"{api_url}/projects/{quote_plus(project)}/pipeline",
        headers={
            "PRIVATE-TOKEN": token,
        },
        json={
            "ref": ref,
            "variables": [
                {
                    "key": key,
                    "secret_value": value,
                    "variable_type": "env_var",
                }
                for key, value in variables.items()
            ]
        },
    )
    if response.status_code != 201:
        raise UsageError(f'GitLab error: {response.content.decode("utf-8")}')
    else:
        return response.json()["web_url"]
