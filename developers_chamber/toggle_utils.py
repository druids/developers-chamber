import math
import time
from datetime import date, timedelta
from urllib.error import HTTPError

import click
from attrdict import AttrDict
from toggl.TogglPy import Toggl


def _get_toggl_client(api_key):
    client = Toggl()
    client.setAPIKey(api_key)
    try:
        client.getWorkspaces()
    except HTTPError:
        raise click.BadParameter('Invalid api key or connection problem')
    return client


def start_timer(api_key, description):
    client = _get_toggl_client(api_key)
    return AttrDict(client.startTimeEntry(description)['data'])


def stop_running_timer(api_key):
    client = _get_toggl_client(api_key)
    current_timer_data = get_running_timer_data(api_key)
    if current_timer_data:
        return AttrDict(client.stopTimeEntry(current_timer_data.id)['data'])
    else:
        return None


def get_running_timer_data(api_key):
    client = _get_toggl_client(api_key)
    current_timer = client.currentRunningTimeEntry()
    return AttrDict(current_timer['data']) if current_timer['data'] else None


def _prepare_report_data(client, description=None, from_date=None, to_date=None):
    from_date = from_date or date.today()
    to_date = to_date or date.today()

    if to_date - from_date > timedelta(days=366):
        raise click.BadParameter('Invalid filter parameters. You can generate reports with max 1 year timedelta')

    data = {
        'workspace_id': client.getWorkspaces()[0]['id'],
        'since': str(from_date),
        'until': str(to_date),
    }
    if description:
        data['description'] = description
    return data


def get_timer_report(api_key, description=None, from_date=None, to_date=None):
    client = _get_toggl_client(api_key)
    data = _prepare_report_data(client, description, from_date, to_date)
    return AttrDict(client.getDetailedReport(data))


def get_full_timer_report(api_key, description=None, from_date=None, to_date=None):
    client = _get_toggl_client(api_key)
    data = _prepare_report_data(client, description, from_date, to_date)

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
    return AttrDict(report_data)
