import json
import logging
import math
import os
import platform
import re
import shutil
import signal
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path, PurePath

from click import BadParameter, ClickException, confirm
from click.exceptions import Exit
from python_hosts.exception import UnableToWriteHosts
from python_hosts.hosts import Hosts, HostsEntry

from developers_chamber.utils import (
    CommandError,
    call_command,
    call_compose_command,
    pretty_time_delta,
    INSTALLED_MODULES,
)

LOGGER = logging.getLogger()


ISSUE_KEY_PATTERN = re.compile(r"(?P<issue_key>[A-Z][A-Z]+-\d+).*")


if (
    "jira" in INSTALLED_MODULES
    and "git" in INSTALLED_MODULES
    and "toggle" in INSTALLED_MODULES
):
    from developers_chamber.git_utils import get_current_branch_name
    from developers_chamber.jira_utils import (
        clean_issue_key,
        get_issue_fields,
        log_issue_time,
    )
    from developers_chamber.toggle_utils import (
        check_workspace_and_project,
        get_full_timer_report,
        get_running_timer_data,
        start_timer,
        stop_running_timer,
    )
    from developers_chamber.bitbucket_utils import (
        create_pull_request as bitbucket_create_pull_request,
    )

    def _get_timer_comment(timer):
        return "Toggl #{}".format(timer["id"])

    def start_task(
        jira_url,
        jira_username,
        jira_api_key,
        jira_project_key,
        toggl_api_key,
        toggl_workspace_id,
        toggl_project_id,
        issue_key,
    ):
        running_timer = get_running_timer_data(toggl_api_key)
        if running_timer:
            # Do not stop timer if toggl workspace or project is invalid
            check_workspace_and_project(
                toggl_api_key, toggl_workspace_id, toggl_project_id
            )
            if confirm("Timer is already running do you want to log it?"):
                stop_task(jira_url, jira_username, jira_api_key, toggl_api_key)

        issue_key = clean_issue_key(issue_key, jira_project_key)
        issue_data = get_issue_fields(
            jira_url, jira_username, jira_api_key, issue_key, jira_project_key
        )
        toggl_description = "{} {}".format(issue_key, issue_data.summary)
        start_timer(
            toggl_api_key, toggl_description, toggl_workspace_id, toggl_project_id
        )
        return 'Toggle was started with description "{}"'.format(toggl_description)

    def create_or_update_pull_request(
        jira_url,
        jira_username,
        jira_api_key,
        bitbucket_username,
        bitbucket_password,
        bitbucket_destination_branch_name,
        bitbucket_repository_name,
    ):
        issue_key = clean_issue_key()
        issue_data = get_issue_fields(jira_url, jira_username, jira_api_key, issue_key)
        return bitbucket_create_pull_request(
            bitbucket_username,
            bitbucket_password,
            "{} {}".format(issue_key, issue_data.summary),
            "",
            get_current_branch_name(),
            bitbucket_destination_branch_name,
            bitbucket_repository_name,
        )

    def stop_task(jira_url, jira_username, jira_api_key, toggl_api_key):
        running_timer = get_running_timer_data(toggl_api_key)
        if running_timer:
            match = ISSUE_KEY_PATTERN.match(running_timer["description"])
            if match:
                issue_key = match.group("issue_key")
                get_issue_fields(jira_url, jira_username, jira_api_key, issue_key)
                stopped_timer = stop_running_timer(toggl_api_key)
                log_issue_time(
                    jira_url,
                    jira_username,
                    jira_api_key,
                    issue_key,
                    time_spend=timedelta(seconds=stopped_timer["duration"]),
                    comment=_get_timer_comment(stopped_timer),
                )
                return "Timer was stopped and time was logged"
            else:
                ClickException("Invalid running task description")
        else:
            ClickException("No running task")

    def sync_timer_to_jira(
        jira_url,
        jira_username,
        jira_api_key,
        toggl_api_key,
        toggl_workspace_id,
        toggl_project_id,
        from_date,
        to_date,
    ):
        def get_timer_worklog(timer, issue_data):
            for worklog in issue_data.worklog.worklogs:
                if hasattr(
                    worklog, "comment"
                ) and worklog.comment == _get_timer_comment(timer):
                    return worklog
            return None

        timers = get_full_timer_report(
            toggl_api_key,
            workspace_id=toggl_workspace_id,
            project_id=toggl_project_id,
            from_date=from_date,
            to_date=to_date,
        )["data"]
        for timer in timers:
            match = ISSUE_KEY_PATTERN.match(timer["description"])
            if match:
                issue_key = match.group("issue_key")
                issue_data = get_issue_fields(
                    jira_url, jira_username, jira_api_key, issue_key
                )
                timer_worklog = get_timer_worklog(timer, issue_data)

                timer_seconds = (
                    math.ceil(timer["dur"] / 1000 / 60) * 60
                )  # Rounded on minutes
                if timer_worklog and timer_worklog.timeSpentSeconds != timer_seconds:
                    timer_worklog.delete()
                    LOGGER.info(
                        'Updating issue "{}" worklog "{}"'.format(
                            issue_key, pretty_time_delta(timer_seconds)
                        )
                    )
                    log_issue_time(
                        jira_url,
                        jira_username,
                        jira_api_key,
                        issue_key,
                        time_spend=timedelta(seconds=timer_seconds),
                        comment=_get_timer_comment(timer),
                    )
                elif not timer_worklog:
                    LOGGER.info(
                        'Adding issue "{}" worklog "{}"'.format(
                            issue_key, pretty_time_delta(timer_seconds)
                        )
                    )
                    log_issue_time(
                        jira_url,
                        jira_username,
                        jira_api_key,
                        issue_key,
                        time_spend=timedelta(seconds=timer_seconds),
                        comment=_get_timer_comment(timer),
                    )


def get_command_output(command, quiet=False, env=None):
    env = {} if env is None else env
    try:
        if not quiet:
            LOGGER.info(command if isinstance(command, str) else " ".join(command))
        return subprocess.check_output(
            command, shell=isinstance(command, str), env=dict(os.environ, **env)
        )
    except subprocess.CalledProcessError:
        raise ClickException("Command returned error")


def set_hosts(domains):
    try:
        hosts = Hosts()
        hosts.add([HostsEntry(entry_type="ipv4", address="127.0.0.1", names=domains)])
        hosts.write()
    except UnableToWriteHosts:
        raise ClickException(
            'Unable to write to hosts file. Please call command with "sudo".'
        )


def _call_compose_command(
    project_name,
    compose_files,
    command,
    containers=None,
    extra_command=None,
    env=None,
    quiet=False,
):
    compose_command = ["docker", "--log-level=ERROR", "compose", "-p", project_name]
    compose_command += ["-f{}".format(f) for f in compose_files]
    if isinstance(command, str):
        compose_command.append(command)
    else:
        compose_command += list(command)
    compose_command += list(containers) if containers else []
    if extra_command:
        compose_command.append(extra_command)
    return call_compose_command(compose_command, quiet=quiet, env=env)


def copy_containers_dirs(project_name, containers_dir_to_copy=None, containers=None):
    for container_name, _, host_dir in containers_dir_to_copy:
        if not containers or container_name in containers:
            shutil.rmtree(Path.cwd() / host_dir, ignore_errors=True)
            os.makedirs(Path.cwd() / host_dir)

    for container_name, container_dir, host_dir in containers_dir_to_copy:
        if not containers or container_name in containers:
            call_command(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    "{}:/copy_tmp".format(Path.cwd() / host_dir),
                    "-u",
                    str(os.getuid()),
                    "{}-{}".format(project_name, container_name),
                    "cp -rT {}/ /copy_tmp/".format(container_dir),
                ]
            )


def compose_build(
    project_name, compose_files, containers=None, containers_dir_to_copy=None, env=None
):
    _call_compose_command(project_name, compose_files, "build", containers, env=env)

    if containers_dir_to_copy:
        copy_containers_dirs(project_name, containers_dir_to_copy, containers)


def _run_containers(project_name, compose_files, containers, command, env=None):
    for container in containers:
        _call_compose_command(
            project_name,
            compose_files,
            ["run", "--use-aliases", "--rm"],
            [container],
            command,
            env=env,
        )


def compose_run(project_name, compose_files, containers, command, env=None, down=True):
    usage = {"services": list(containers), "dependencies_only": True}
    with _project_usage(project_name, compose_files, usage, down, env):
        try:
            _run_containers(project_name, compose_files, containers, command, env=env)
        except CommandError as error:
            # The command reported its failure itself, pydev only passes its return code on.
            raise Exit(error.exit_code)


def compose_exec(project_name, compose_files, containers, command, env=None):
    for container in containers:
        _call_compose_command(
            project_name, compose_files, "exec", [container], command, env=env
        )


def compose_kill_all():
    if get_command_output("docker ps -q"):
        call_command("docker kill $(docker ps -q)")


def compose_up(project_name, compose_files, containers, env=None, down=True):
    """
    Start the containers detached and follow their logs, so that Ctrl+C does not stop services
    which other pydev processes of the project still need.
    """
    usage = {"services": list(containers or ()), "dependencies_only": False}
    with _project_usage(project_name, compose_files, usage, down, env):
        if _call_compose_command(
            project_name, compose_files, ["up", "--detach"], containers, env=env
        ):
            _call_compose_command(
                project_name, compose_files, ["logs", "--follow"], containers, env=env
            )


def _users_directory(project_name):
    """Registry of the pydev processes using the project, in a directory cleared on reboot."""
    runtime = os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()
    return Path(runtime) / "pydev-{}".format(os.getuid()) / "compose" / project_name


def _is_running(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _other_users(directory):
    """Usages of the other running pydev processes of the project, dropping finished ones."""
    users = {}
    for user in directory.iterdir():
        if not user.name.isdigit() or int(user.name) == os.getpid():
            continue
        if _is_running(int(user.name)):
            users[user.name] = json.loads(user.read_text() or "{}")
        else:
            user.unlink(missing_ok=True)
    return users


def _compose_dependencies(project_name, compose_files, env=None):
    """Services of the compose files mapped to the services they directly depend on."""
    command = ["docker", "--log-level=ERROR", "compose", "-p", project_name]
    command += ["-f{}".format(f) for f in compose_files]
    command += ["config", "--format", "json"]
    services = json.loads(get_command_output(command, quiet=True, env=env))["services"]
    return {
        name: set(service.get("depends_on", {})) for name, service in services.items()
    }


def _needed_services(usage, dependencies):
    """Services which must keep running for the usage, empty services meaning all of them."""
    services = set(usage.get("services") or dependencies)
    needed = set() if usage.get("dependencies_only") else set(services)
    pending = list(services)
    while pending:
        for dependency in dependencies.get(pending.pop(), ()):
            if dependency not in needed:
                needed.add(dependency)
                pending.append(dependency)
    return needed


def _stop_services_unused_by(users, project_name, compose_files, env=None):
    dependencies = _compose_dependencies(project_name, compose_files, env)
    needed = set()
    for usage in users.values():
        needed |= _needed_services(usage, dependencies)
    unused = sorted(set(dependencies) - needed)
    if unused:
        LOGGER.info(
            "Pydev processes %s still use the project, stopping services they do not need",
            ", ".join(users),
        )
        compose_stop(project_name, compose_files, unused, quiet=True)
    else:
        LOGGER.info(
            "Pydev processes %s still use the project, all its services are kept",
            ", ".join(users),
        )


def _detach_from_terminal():
    """Point the standard streams to /dev/null once the terminal is gone, so writes do not fail."""
    devnull = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(devnull, fd)


def _exit_on_signal(signum, frame):
    for handled in (signal.SIGHUP, signal.SIGTERM):
        signal.signal(handled, signal.SIG_IGN)
    if signum == signal.SIGHUP:
        _detach_from_terminal()
    raise SystemExit(128 + signum)


@contextmanager
def _exit_on_hangup_and_terminate():
    """Turn SIGHUP and SIGTERM into SystemExit so that the cleanup in finally blocks runs."""
    previous = {
        handled: signal.signal(handled, _exit_on_signal)
        for handled in (signal.SIGHUP, signal.SIGTERM)
    }
    try:
        yield
    finally:
        for handled, handler in previous.items():
            signal.signal(handled, handler)


@contextmanager
def _project_usage(project_name, compose_files, usage, down, env=None):
    """
    Register the process and the services it needs as a user of the project. The first user cleans
    leftovers, a leaving user stops what the others do not need and the last one runs down.
    """
    directory = _users_directory(project_name)
    directory.mkdir(parents=True, exist_ok=True)
    own = directory / str(os.getpid())
    own.write_text(json.dumps(usage))
    with _exit_on_hangup_and_terminate():
        try:
            if down and not _other_users(directory):
                compose_down(project_name, compose_files, quiet=True)
            yield
        finally:
            own.unlink(missing_ok=True)
            users = _other_users(directory)
            if users:
                _stop_services_unused_by(users, project_name, compose_files, env)
            elif down:
                compose_down(project_name, compose_files, quiet=True)
            elif not usage["dependencies_only"]:
                compose_stop(project_name, compose_files, None, quiet=True)


def compose_stop(project_name, compose_files, containers, quiet=False):
    _call_compose_command(project_name, compose_files, "stop", containers, quiet=quiet)


def compose_down(project_name, compose_files, volumes=False, quiet=False):
    command = ["down", "--remove-orphans"]
    if volumes:
        command.append("--volumes")
    _call_compose_command(project_name, compose_files, command, quiet=quiet)


def docker_clean(all=False):
    call_command(["docker", "image", "prune", "-f"])
    call_command(["docker", "container", "prune", "-f"])
    if all:
        call_command(["docker", "system", "prune", "-af"])
        if get_command_output("docker volume ls -q"):
            call_command("docker volume rm $(docker volume ls -q)")


def _unmount_and_rm_directory(directory):
    if platform.system() == "Darwin":
        call_command(
            'mount -t osxfuse | grep "{}" | awk -F " " \'{{print "umount " $3}}\'| bash'.format(
                directory
            ),
            quiet=True,
        )
    elif platform.system() == "Linux":
        call_command(
            'mount -l -t fuse | grep "{}" | awk -F " " \'{{print "fusermount -u " $3}}\'| bash'.format(
                directory
            ),
            quiet=True,
        )
    shutil.rmtree(directory, ignore_errors=True)


def bind_library(library_source_dir, library_destination_dir):
    source_path_directory = Path(library_source_dir).resolve()
    destination_path_directory = (
        Path(library_destination_dir).resolve() / source_path_directory.name
    )
    _unmount_and_rm_directory(destination_path_directory)
    os.makedirs(destination_path_directory)
    call_command(
        "bindfs --delete-deny {} {}".format(
            source_path_directory, destination_path_directory
        ),
        quiet=True,
    )


def compose_install(
    project_name,
    compose_files,
    var_dirs=None,
    containers_dir_to_copy=None,
    install_container_commands=None,
):
    var_dirs = [Path.cwd() / var_dir for var_dir in var_dirs or ()]

    for var_dir in var_dirs:
        _unmount_and_rm_directory(var_dir)

    for var_dir in var_dirs:
        os.makedirs(var_dir)

    compose_build(
        project_name, compose_files, containers_dir_to_copy=containers_dir_to_copy
    )

    for container_name, command in install_container_commands or ():
        _run_containers(project_name, compose_files, [container_name], command)

    compose_stop(project_name, compose_files, None)
