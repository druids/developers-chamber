import os
from pathlib import Path

import click
import yaml
from developers_chamber.scripts import cli

PYDEV_DIR = Path.cwd() / ".pydev"
BIND_CONF_NAME = "bind.conf"
DOCKER_COMPOSE_BIND_PATH = PYDEV_DIR / "docker-compose.bind.yml"


def _src_path(path):
    if os.path.basename(path) == "src":
        return path
    return os.path.join(path, "src")


def _container_path(path):
    src = _src_path(path)
    segment = os.path.basename(os.path.dirname(src))
    return f"/app/libs/{segment}"


def _read_paths():
    if not DOCKER_COMPOSE_BIND_PATH.exists():
        return []
    with open(DOCKER_COMPOSE_BIND_PATH) as f:
        data = yaml.safe_load(f)
    try:
        volumes = data["services"]["app"]["volumes"] or []
        return [v.split(":")[0] for v in volumes]
    except (KeyError, TypeError):
        return []


def _write_paths(paths):
    _write_docker_compose(paths)


def _write_docker_compose(paths):
    PYDEV_DIR.mkdir(exist_ok=True)
    volumes = [f"{_src_path(p)}:{_container_path(p)}" for p in paths]
    data = {
        "services": {
            "app": {
                "volumes": volumes,
            }
        },
    }
    with open(DOCKER_COMPOSE_BIND_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


@cli.group()
def bind():
    """Manage bound Python library source paths."""


@bind.command()
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
)
def add(path):
    """Add a Python library source path to bound dependencies."""
    is_src = os.path.basename(path) == "src"
    has_src = os.path.isdir(os.path.join(path, "src"))
    if not is_src and not has_src:
        raise click.BadParameter(
            f"'{path}' must be a 'src' folder or contain a 'src' subfolder."
        )
    src = _src_path(path)
    paths = _read_paths()
    if src not in paths:
        paths.append(src)
        _write_paths(paths)
        click.echo(f"Added: {src}")
    else:
        click.echo(f"Already bound: {src}")


@bind.command()
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
)
def remove(path):
    """Remove a Python library source path from bound dependencies."""
    src = _src_path(path)
    paths = _read_paths()
    if src in paths:
        paths.remove(src)
        _write_paths(paths)
        click.echo(f"Removed: {src}")
    else:
        click.echo(
            f"Not found in bound paths: {src}\n Use `pydev bind list` to view bound paths."
        )


@bind.command(name="init")
def bind_init():
    """Initialize bind configuration in .pydev/."""
    PYDEV_DIR.mkdir(exist_ok=True)

    conf_path = PYDEV_DIR / BIND_CONF_NAME
    if not conf_path.exists():
        if click.confirm("bind.conf not found. Create it?", default=True):
            base_files = os.environ.get("PROJECT_DOCKER_COMPOSE_FILES")
            if base_files:
                compose_value = (
                    "${PROJECT_DOCKER_COMPOSE_FILES},.pydev/docker-compose.bind.yml"
                )
            else:
                compose_value = ".pydev/docker-compose.bind.yml"
            conf_path.write_text(f"PROJECT_DOCKER_COMPOSE_FILES={compose_value}\n")
            click.echo(f"Created: {conf_path}")
    else:
        click.echo(f"Already exists: {conf_path}")

    gitignore_path = PYDEV_DIR / ".gitignore"
    entries = {BIND_CONF_NAME, f"~{BIND_CONF_NAME}", "docker-compose.bind.yml"}
    existing = (
        set(gitignore_path.read_text().splitlines())
        if gitignore_path.exists()
        else set()
    )
    new_entries = entries - existing
    if new_entries:
        with gitignore_path.open("a") as f:
            f.write("\n".join(sorted(new_entries)) + "\n")
        click.echo(f"Updated .gitignore: added {', '.join(sorted(new_entries))}")
    else:
        click.echo(".gitignore already up to date.")


@bind.command(name="on")
def bind_on():
    """Enable bind by restoring bind.conf from ~bind.conf."""
    disabled = PYDEV_DIR / f"~{BIND_CONF_NAME}"
    enabled = PYDEV_DIR / BIND_CONF_NAME
    if enabled.exists():
        click.echo("Already enabled")
        return
    if disabled.exists():
        disabled.rename(enabled)
        click.echo("Bind enabled.")
    else:
        click.echo("Configuration missing: neither bind.conf nor ~bind.conf not found.")


@bind.command(name="off")
def bind_off():
    """Disable bind by renaming bind.conf to ~bind.conf."""
    enabled = PYDEV_DIR / BIND_CONF_NAME
    disabled = PYDEV_DIR / f"~{BIND_CONF_NAME}"
    if disabled.exists():
        click.echo("Already disabled")
        return
    if enabled.exists():
        enabled.rename(disabled)
        click.echo("Bind disabled.")
    else:
        click.echo("Configuration missing: neither bind.conf nor ~bind.conf not found.")


@bind.command(name="list")
def list_deps():
    """List all currently bound dependency paths."""
    paths = _read_paths()
    if paths:
        for p in paths:
            click.echo(p)
    else:
        click.echo("No dependencies bound.")
