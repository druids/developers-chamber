import math
import time
from datetime import date, timedelta
from urllib.error import HTTPError

import click
from toggl.TogglPy import Toggl, Endpoints


def _get_toggl_client(api_key):
    client = Toggl()
    client.setAPIKey(api_key)

    try:
        client.getWorkspaces()
    except HTTPError:
        raise click.BadParameter('Invalid api key or connection problem')
    return client


def _get_workspace(client, workspace_id, project_id):
    if project_id:
        try:
            project_workspace_id = client.getProject(project_id)['data']['wid']
            if workspace_id and workspace_id != project_workspace_id:
                raise click.BadParameter('Project ID is not part of workspace')
            return project_workspace_id
        except HTTPError:
            raise click.BadParameter('Project ID is invalid')
    elif workspace_id:
        if client.getWorkspace(id=workspace_id):
            return workspace_id
        else:
            raise click.BadParameter('Workspace ID is invalid')
    else:
        return client.getWorkspaces()[0]['id']


def check_workspace_and_project(api_key, workspace_id, project_id):
    client = _get_toggl_client(api_key)
    _get_workspace(client, workspace_id, project_id)


def start_timer(api_key, description, workspace_id=None, project_id=None):
    client = _get_toggl_client(api_key)
    workspace_id = _get_workspace(client, workspace_id, project_id)

    data = {
        'time_entry': {
            'created_with': client.user_agent,
            'description': description
        }
    }
    if project_id:
        data['time_entry']['pid'] = project_id
    if workspace_id:
        data['time_entry']['wid'] = workspace_id
    return client.decodeJSON(client.postRequest(Endpoints.START_TIME, parameters=data))['data']


def stop_running_timer(api_key):
    client = _get_toggl_client(api_key)
    current_timer_data = get_running_timer_data(api_key)
    if current_timer_data:
        return client.stopTimeEntry(current_timer_data['id'])['data']
    else:
        return None


def get_running_timer_data(api_key):
    breakpoint()
    client = _get_toggl_client(api_key)
    current_timer = client.currentRunningTimeEntry()
    return current_timer['data'] if current_timer['data'] else None


def _prepare_report_data(client, workspace_id=None, project_id=None, description=None, from_date=None, to_date=None):
    from_date = from_date or date.today()
    to_date = to_date or date.today()

    if to_date - from_date > timedelta(days=366):
        raise click.BadParameter('Invalid filter parameters. You can generate reports with max 1 year timedelta')

    workspace_id = _get_workspace(client, workspace_id, project_id)

    data = {
        'workspace_id': workspace_id,
        'since': str(from_date),
        'until': str(to_date),
        'pid': project_id
    }
    if project_id:
        data['project_ids'] = project_id

    if description:
        data['description'] = description
    return data


def get_timer_report(api_key, workspace_id=None, project_id=None, description=None, from_date=None, to_date=None):
    client = _get_toggl_client(api_key)
    data = _prepare_report_data(client, workspace_id, project_id, description, from_date, to_date)
    return client.getDetailedReport(data)


def get_full_timer_report(api_key, workspace_id=None, project_id=None, description=None, from_date=None, to_date=None):
    client = _get_toggl_client(api_key)
    data = _prepare_report_data(client, workspace_id, project_id, description, from_date, to_date)

    pages_index = 1
    data['page'] = pages_index
    report_data = client.getDetailedReport(data)
    pages_number = (
        math.ceil(report_data.get('total_count', 0) / report_data.get('per_page', 0))
        if report_data.get('per_page', 0) != 0 else 0
    )
    for pages_index in range(2, pages_number + 1):
        time.sleep(1)  # There is rate limiting of 1 request per second (per IP per API token).
        data['page'] = pages_index
        report_data['data'].extend(client.getDetailedReport(data)['data'])
    return report_data
