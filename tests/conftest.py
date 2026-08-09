import json
import os

import pytest


@pytest.fixture(autouse=True)
def restore_environ():
    """
    Keep the environment of one test out of the others.

    Loading a configuration writes arbitrary variables into ``os.environ``, which monkeypatch
    cannot undo because it does not know about them.
    """
    original = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original)


@pytest.fixture
def config_path(tmp_path):
    """Directory of a throwaway project which holds a .pydev configuration directory."""
    (tmp_path / ".pydev").mkdir()
    return tmp_path


@pytest.fixture
def config_dir(config_path):
    return config_path / ".pydev"


@pytest.fixture
def write_config(config_dir):
    def write(name, content):
        file = config_dir / name
        file.write_text(content)
        return file

    return write


@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    """Empty directory which is the working directory of the test."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def version_file(project_dir):
    """Writes a version file into the working directory and reads it back."""

    class VersionFile:
        path = project_dir

        def write(self, name, content):
            (project_dir / name).write_text(content)
            return name

        def write_version(self, version, name="version.json"):
            return self.write(name, json.dumps({"version": version}))

        def read_version(self, name="version.json"):
            return json.loads((project_dir / name).read_text())["version"]

    return VersionFile()


@pytest.fixture
def git_repo(project_dir):
    """Throwaway git repository with a single commit on the master branch."""
    git = pytest.importorskip("git", reason='requires the "git" extra')

    repo = git.Repo.init(project_dir)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test")
        config.set_value("user", "email", "test@example.com")
    (project_dir / "version.json").write_text(json.dumps({"version": "1.2.3"}))
    repo.index.add(["version.json"])
    repo.index.commit("Initial commit")
    repo.git.branch("-M", "master")
    return repo
