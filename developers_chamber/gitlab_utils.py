from urllib.parse import quote_plus

import time
import requests
from click import UsageError
from urllib.parse import quote


def _auth_headers(token=None, job_token=None):
    """
    A CI job token is accepted only by a part of the API (the Releases endpoints among them),
    so it is used when it is available and the private token stays the fallback.
    """
    if job_token:
        return {"JOB-TOKEN": job_token}
    if token:
        return {"PRIVATE-TOKEN": token}
    raise UsageError("GitLab token or job token is required")


def create_merge_request(
    url,
    token,
    title,
    description,
    source_branch,
    target_branch,
    project,
    assignee_id=None,
    automerge=False,
    remove_source_branch=False,
):
    response = requests.post(
        f"{url}/api/v4/projects/{quote_plus(project)}/merge_requests",
        headers=_auth_headers(token),
        json={
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
            "assignee_id": assignee_id,
            "remove_source_branch": remove_source_branch,
        },
    )

    if response.status_code != 201:
        raise UsageError(f'GitLab error: {response.content.decode("utf-8")}')

    if automerge:
        message = activate_automerge(url, token, project, response.json()["iid"])
        return f"{response.json()['web_url']} ({message})"

    return response.json()["web_url"]


def activate_automerge(url, token, project, merge_request_id, retries=5):
    for _ in range(retries):
        merge_response = requests.put(
            f"{url}/api/v4/projects/{quote_plus(project)}/merge_requests/{merge_request_id}/merge",
            json={"merge_when_pipeline_succeeds": True},
            headers=_auth_headers(token),
        )
        if merge_response.status_code == 200:
            return "Automerge activated"
        time.sleep(5)
    return "Automerge activation failed"


def run_job(url, token, project, ref, variables):
    response = requests.post(
        f"{url}/api/v4/projects/{quote_plus(project)}/pipeline",
        headers=_auth_headers(token),
        json={
            "ref": ref,
            "variables": [
                {
                    "key": key,
                    "value": value,
                    "variable_type": "env_var",
                }
                for key, value in variables.items()
            ],
        },
    )
    if response.status_code != 201:
        raise UsageError(f'GitLab error: {response.content.decode("utf-8")}')
    else:
        return response.json()["web_url"]


def get_project_id(url, project, token):
    response = requests.get(
        f"{url}/api/v4/projects/{quote_plus(project)}",
        headers={
            **_auth_headers(token),
            "Content-type": "application/json",
        },
    )
    if response.status_code != 200:
        raise UsageError(f'GitLab error: {response.content.decode("utf-8")}')
    else:
        return response.json()["id"]


def _release_record_name(tag_name):
    """
    The release is named after its tag, so a monorepo release page reads as a changelog feed:
    "lib-a@1.3.0" -> "lib-a 1.3.0", a tag without a prefix stays as it is.
    """
    return tag_name.replace("@", " ", 1)


def parse_asset_links(assets):
    """Turn the "name=URL" options into the assets links of the Releases API."""
    links = []
    for asset in assets:
        # The URL may carry a query string, so only the first "=" separates the name.
        name, _, url = asset.partition("=")
        if not name or not url:
            raise UsageError(
                f'Invalid asset "{asset}", the expected format is "name=URL"'
            )
        links.append({"name": name, "url": url})
    return links


def create_release_record(
    url,
    project,
    tag_name,
    name=None,
    description=None,
    asset_links=None,
    token=None,
    job_token=None,
):
    data = {
        "tag_name": tag_name,
        "name": name or _release_record_name(tag_name),
    }
    if description:
        data["description"] = description
    if asset_links:
        data["assets"] = {"links": list(asset_links)}

    response = requests.post(
        f"{url}/api/v4/projects/{quote_plus(project)}/releases",
        headers=_auth_headers(token, job_token),
        json=data,
    )
    if response.status_code != 201:
        raise UsageError(f'GitLab error: {response.content.decode("utf-8")}')
    else:
        return response.json().get("_links", {}).get("self") or tag_name
