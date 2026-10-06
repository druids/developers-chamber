import json
import os
import signal
import subprocess
import sys
from types import SimpleNamespace

import pytest
from click import ClickException
from click.exceptions import Exit

from developers_chamber import project_utils
from developers_chamber.utils import CommandError

UP = ["up", "--detach"]
LOGS = ["logs", "--follow"]
RUN = ["run", "--use-aliases", "--rm", "app"]
DOWN = ["down", "--remove-orphans"]
CONFIG = {
    "services": {
        "app": {"depends_on": {"db": {}}},
        "db": {"depends_on": {"redis": {}}},
        "redis": {},
        "web": {},
        "worker": {"depends_on": {"db": {}}},
    }
}
UP_ALL = {"services": [], "dependencies_only": False}
UP_WEB = {"services": ["web"], "dependencies_only": False}
RUN_APP = {"services": ["app"], "dependencies_only": True}


@pytest.fixture
def users(tmp_path, monkeypatch):
    """Directory where pydev processes register as users of the project."""
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    directory = tmp_path / "pydev-{}".format(os.getuid()) / "compose" / "demo"
    directory.mkdir(parents=True)

    def register(usage, pid=os.getppid()):
        (directory / str(pid)).write_text(json.dumps(usage))

    return SimpleNamespace(directory=directory, register=register)


@pytest.fixture
def calls(monkeypatch):
    """
    Compose commands recorded instead of being run, with their services.

    `calls.during` runs inside the command which up or run waits on.
    """

    class Calls(list):
        quiet = []
        during = None
        fails = False
        interrupted = False

    calls = Calls()

    def fake_call_compose_command(
        project_name, compose_files, command, containers=None, *args, **kwargs
    ):
        command = [command] if isinstance(command, str) else list(command)
        calls.append(command + list(containers or ()))
        if kwargs.get("quiet"):
            calls.quiet.append(calls[-1])
        if command == UP and calls.interrupted:
            return False
        if command in (UP, RUN[:-1]) and calls.fails:
            raise CommandError(3)
        if command in (LOGS, RUN[:-1]) and calls.during:
            calls.during()
        return True

    monkeypatch.setattr(
        project_utils, "_call_compose_command", fake_call_compose_command
    )
    monkeypatch.setattr(
        project_utils,
        "get_command_output",
        lambda command, quiet=False, env=None: json.dumps(CONFIG).encode(),
    )
    return calls


@pytest.fixture
def finished_pid():
    process = subprocess.Popen([sys.executable, "-c", ""])
    process.wait()
    return process.pid


def up(**kwargs):
    project_utils.compose_up("demo", ["compose.yml"], None, **kwargs)


def run(**kwargs):
    project_utils.compose_run("demo", ["compose.yml"], ["app"], "bash", **kwargs)


@pytest.mark.parametrize(
    ("command", "own_calls"), [(up, [UP, LOGS]), (run, [RUN])], ids=["up", "run"]
)
def test_only_user_cleans_leftovers_and_removes_the_project(
    users, calls, command, own_calls
):
    command()

    assert calls == [DOWN, *own_calls, DOWN]
    assert list(users.directory.iterdir()) == []


def test_only_the_run_itself_is_logged(users, calls):
    run()

    assert calls.quiet == [DOWN, DOWN]


def test_up_keeps_the_dependencies_of_a_running_shell(users, calls):
    users.register(RUN_APP)

    up()

    assert calls == [UP, LOGS, ["stop", "app", "web", "worker"]]


def test_shell_keeps_everything_of_a_running_up(users, calls):
    users.register(UP_ALL)

    run()

    assert calls == [RUN]


def test_shell_stops_its_dependencies_unused_by_a_running_up(users, calls):
    users.register(UP_WEB)

    run()

    assert calls == [RUN, ["stop", "app", "db", "redis", "worker"]]


def test_project_used_by_a_process_started_meanwhile_is_kept(users, calls):
    calls.during = lambda: users.register(UP_ALL)

    run()

    assert calls == [DOWN, RUN]


def test_process_is_registered_with_its_services_while_it_runs(users, calls):
    registered = {}
    calls.during = lambda: registered.update(
        {p.name: json.loads(p.read_text()) for p in users.directory.iterdir()}
    )

    run()

    assert registered == {str(os.getpid()): RUN_APP}


def test_finished_process_does_not_keep_the_project(users, calls, finished_pid):
    users.register(UP_ALL, pid=finished_pid)

    up()

    assert calls == [DOWN, UP, LOGS, DOWN]
    assert list(users.directory.iterdir()) == []


def test_up_only_stops_the_project_when_down_is_disabled(users, calls):
    up(down=False)

    assert calls == [UP, LOGS, ["stop"]]


def test_run_keeps_its_dependencies_when_down_is_disabled(users, calls):
    run(down=False)

    assert calls == [RUN]


def test_project_is_removed_after_a_failure(users, calls):
    calls.fails = True

    with pytest.raises(ClickException):
        up()

    assert calls == [DOWN, UP, DOWN]


def test_failed_run_exits_with_the_return_code_of_the_command(users, calls):
    calls.fails = True

    with pytest.raises(Exit) as exit:
        run()

    assert exit.value.exit_code == 3
    assert calls == [DOWN, RUN, DOWN]


def test_interrupted_start_does_not_follow_the_logs(users, calls):
    calls.interrupted = True

    up()

    assert calls == [DOWN, UP, DOWN]


@pytest.mark.parametrize(
    ("signum", "detached"),
    [(signal.SIGTERM, False), (signal.SIGHUP, True)],
    ids=["terminate", "hangup"],
)
def test_project_is_removed_after_a_signal(users, calls, monkeypatch, signum, detached):
    detaches = []
    monkeypatch.setattr(
        project_utils, "_detach_from_terminal", lambda: detaches.append(True)
    )
    calls.during = lambda: os.kill(os.getpid(), signum)

    with pytest.raises(SystemExit) as exit:
        up()

    assert exit.value.code == 128 + signum
    assert calls == [DOWN, UP, LOGS, DOWN]
    assert bool(detaches) == detached


def test_signal_handlers_are_restored(users, calls):
    previous = signal.getsignal(signal.SIGTERM), signal.getsignal(signal.SIGHUP)

    up()

    assert (
        signal.getsignal(signal.SIGTERM),
        signal.getsignal(signal.SIGHUP),
    ) == previous


def test_down_removes_volumes_on_request(calls):
    project_utils.compose_down("demo", ["compose.yml"], volumes=True)

    assert calls == [DOWN + ["--volumes"]]
