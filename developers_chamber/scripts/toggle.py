import os
from datetime import date

import click

from developers_chamber.scripts import cli
from developers_chamber.toggle_utils import (get_full_timer_report,
                                             get_running_timer_data,
                                             get_timer_report, start_timer,
                                             stop_running_timer)
from developers_chamber.utils import pretty_time_delta

api_key = os.environ.get('TOGGL_API_KEY')


@cli.group()
def toggl():
    """
    Toggl commands.
    """


@toggl.command()
@click.option('--description', '-d',  help='task description', type=str, required=True)
@click.option('--api-key', '-k',  help='toggle API key', type=str, required=True, default=api_key)
def start(description, api_key):
    """
    Start toggl timer.
    """
    running_timer = start_timer(api_key, description)
    click.echo('Timer with description "{}" was started'.format(running_timer.description))


@toggl.command()
@click.option('--api-key', '-k',  help='toggle API key', type=str, required=True, default=api_key)
def stop(api_key):
    """
    Stop toggl timer.
    """
    stopped_timer = stop_running_timer(api_key)
    if stopped_timer:
        click.echo('Timer with description "{}" was stopped. Duration: "{}s"'.format(
            stopped_timer.description, pretty_time_delta(stopped_timer.duration)
        ))
    else:
        click.echo('No running timer')


@toggl.command(name='print')
@click.option('--api-key', '-k',  help='toggle API key', type=str, required=True, default=api_key)
def print_toggl(api_key):
    """
    Print currently running timer detail.
    """
    running_timer = get_running_timer_data(api_key)
    if running_timer:
        for k, v in running_timer.items():
            click.echo("    {:<15}\t{}".format(k + ':', v))
    else:
        click.echo('No running timer')


@toggl.command()
@click.option('--description', '-d',  help='task description', type=str)
@click.option('--from-date', '-f',  help='report from', type=click.DateTime(formats=["%Y-%m-%d"]),
              default=str(date.today()))
@click.option('--to-date', '-t',  help='report to', type=click.DateTime(formats=["%Y-%m-%d"]),
              default=str(date.today()))
@click.option('--api-key', '-k',  help='toggle API key', type=str, required=True, default=api_key)
def print_report(description, from_date, to_date, api_key):
    """
    Print report.
    """
    report_data = get_timer_report(api_key, description, from_date.date(), to_date.date())
    click.echo('    {:<15}\t{}'.format('total time:', pretty_time_delta(report_data.total_grand or 0 / 1000)))
    click.echo('    {:<15}\t{}'.format('timers count:', report_data.total_count))


@toggl.command()
@click.option('--description', '-d',  help='task description', type=str)
@click.option('--from-date', '-f',  help='report from', type=click.DateTime(formats=["%Y-%m-%d"]),
              default=str(date.today()))
@click.option('--to-date', '-t',  help='report to', type=click.DateTime(formats=["%Y-%m-%d"]),
              default=str(date.today()))
@click.option('--api-key', '-k',  help='toggle API key', type=str, required=True, default=api_key)
def print_report_tasks(description, from_date, to_date, api_key):
    """
    Print timer details.
    """
    report_data = get_full_timer_report(api_key, description, from_date.date(), to_date.date())

    click.echo('{:<15} | {}'.format('Time', 'Description'))
    click.echo(16 * '-' + '+' + 16 * '-')
    for timer in report_data.data:
        click.echo('{:<15} | {}'.format(pretty_time_delta(timer.dur / 1000), timer.description))
