import json
import os

import pytest

from developers_chamber.config import (
    ConfigError,
    flatten_settings,
    iter_config_files,
    load_config,
    load_settings_file,
)


class TestFlattenSettings:

    def test_scalars_are_converted_to_upper_case_names_and_strings(self):
        assert flatten_settings(
            {"jira_project_key": "PROJ", "toggl_project_id": 42, "debug": True}
        ) == {"JIRA_PROJECT_KEY": "PROJ", "TOGGL_PROJECT_ID": "42", "DEBUG": "true"}

    def test_false_is_converted_to_false_string(self):
        assert flatten_settings({"debug": False}) == {"DEBUG": "false"}

    def test_nested_objects_are_joined_with_underscore(self):
        assert flatten_settings(
            {"project": {"docker_compose": {"files": "a.yaml"}}}
        ) == {"PROJECT_DOCKER_COMPOSE_FILES": "a.yaml"}

    def test_dashes_in_names_are_normalized_to_underscores(self):
        assert flatten_settings(
            {"project": {"docker-compose": {"var-dirs": "var"}}}
        ) == {"PROJECT_DOCKER_COMPOSE_VAR_DIRS": "var"}

    @pytest.mark.parametrize(
        "data",
        [
            {"project_docker_compose_files": ["a.yaml", "b.yaml"]},
            {"project": {"docker_compose": {"files": ["a.yaml", "b.yaml"]}}},
            {"project": {"docker": {"compose": {"files": ["a.yaml", "b.yaml"]}}}},
        ],
        ids=["flat", "two levels", "three levels"],
    )
    def test_sections_can_be_split_at_any_underscore(self, data):
        assert flatten_settings(data) == {
            "PROJECT_DOCKER_COMPOSE_FILES": "a.yaml,b.yaml"
        }

    def test_lists_are_joined_with_comma(self):
        assert flatten_settings(
            {"version_files": ["version.json", "package.json"]}
        ) == {"VERSION_FILES": "version.json,package.json"}

    def test_empty_list_is_converted_to_empty_string(self):
        assert flatten_settings({"version_files": []}) == {"VERSION_FILES": ""}

    def test_none_value_is_left_out(self):
        assert flatten_settings({"jira_url": None}) == {}

    def test_root_element_must_be_an_object(self):
        with pytest.raises(ConfigError, match="root element must be an object"):
            flatten_settings(["a", "b"])

    @pytest.mark.parametrize(
        ("data", "message"),
        [
            (
                {"project": {"files": {"a"}}},
                'setting "project.files": unsupported value type set',
            ),
            (
                {"project": {"files": [["a"]]}},
                'setting "project.files": unsupported value type list',
            ),
        ],
        ids=["unsupported type", "nested list"],
    )
    def test_invalid_value_is_reported_with_its_path(self, data, message):
        with pytest.raises(ConfigError, match=message):
            flatten_settings(data)


class TestAliasesEncoder:

    def test_object_is_encoded_to_json(self):
        encoded = flatten_settings(
            {
                "aliases": {
                    "up": "project up",
                    "build-js": ["project run -c static", "project run -c base"],
                }
            }
        )["ALIASES"]
        assert json.loads(encoded) == {
            "up": "project up",
            "build-js": ["project run -c static", "project run -c base"],
        }

    def test_alias_names_are_not_normalized(self):
        encoded = flatten_settings({"aliases": {"up-all": "project up -a"}})["ALIASES"]
        assert json.loads(encoded) == {"up-all": "project up -a"}

    def test_alias_with_a_description_is_encoded(self):
        # the form which AliasCommand accepts besides a command and a list of commands
        alias = {"description": "Start the project", "command": "project up"}
        encoded = flatten_settings({"aliases": {"up": alias}})["ALIASES"]
        assert json.loads(encoded) == {"up": alias}

    def test_form_of_a_single_alias_is_left_to_alias_command(self):
        assert json.loads(flatten_settings({"aliases": {"up": 42}})["ALIASES"]) == {
            "up": 42
        }

    def test_json_string_is_kept_as_is(self):
        assert (
            flatten_settings({"aliases": '{"up": "project up"}'})["ALIASES"]
            == '{"up": "project up"}'
        )

    def test_list_is_not_a_valid_value(self):
        with pytest.raises(
            ConfigError,
            match='setting "aliases": must be an object of alias name to command',
        ):
            flatten_settings({"aliases": ["project up"]})


def flatten_docker_compose(setting, value):
    return flatten_settings({"project": {"docker_compose": {setting: value}}})[
        "PROJECT_DOCKER_COMPOSE_{}".format(setting.upper())
    ]


class TestContainersDirToCopyEncoder:

    setting = "containers_dir_to_copy"

    def test_object_is_encoded_to_colon_separated_triples(self):
        assert flatten_docker_compose(
            self.setting,
            {
                "base": {"/usr/local/lib/site-packages": "var/site-packages"},
                "static": {"/srv/node_modules": "var/node_modules"},
            },
        ) == (
            "base:/usr/local/lib/site-packages:var/site-packages,"
            "static:/srv/node_modules:var/node_modules"
        )

    def test_string_is_kept_as_is(self):
        assert flatten_docker_compose(self.setting, "base:/a:var/a") == "base:/a:var/a"

    def test_list_of_strings_is_joined_with_comma(self):
        assert (
            flatten_docker_compose(self.setting, ["base:/a:var/a", "static:/b:var/b"])
            == "base:/a:var/a,static:/b:var/b"
        )

    def test_container_value_must_be_an_object(self):
        with pytest.raises(
            ConfigError,
            match='setting "project.docker_compose.containers_dir_to_copy": container "base"',
        ):
            flatten_docker_compose(self.setting, {"base": "var/site-packages"})

    def test_host_directory_must_be_a_string(self):
        with pytest.raises(ConfigError, match='"/a" must be a string'):
            flatten_docker_compose(self.setting, {"base": {"/a": ["var/a"]}})


class TestContainersInstallCommandEncoder:

    setting = "containers_install_command"

    def test_object_is_encoded_to_colon_separated_pairs(self):
        assert (
            flatten_docker_compose(
                self.setting, {"base": "./manage.py migrate", "static": "build-js.sh"}
            )
            == "base:./manage.py migrate,static:build-js.sh"
        )

    def test_string_is_kept_as_is(self):
        assert (
            flatten_docker_compose(self.setting, "base:./manage.py migrate")
            == "base:./manage.py migrate"
        )

    def test_list_of_strings_is_joined_with_comma(self):
        assert (
            flatten_docker_compose(
                self.setting, ["base:./manage.py migrate", "static:build-js.sh"]
            )
            == "base:./manage.py migrate,static:build-js.sh"
        )

    def test_command_must_be_a_string(self):
        with pytest.raises(ConfigError, match='"base" must be a string'):
            flatten_docker_compose(self.setting, {"base": ["./manage.py migrate"]})


class TestContainersEnvEncoder:

    setting = "containers_env"

    def test_object_is_encoded_to_space_separated_pairs(self):
        assert (
            flatten_docker_compose(self.setting, {"DEBUG": "1", "ENV": "local"})
            == "DEBUG=1 ENV=local"
        )

    def test_string_is_kept_as_is(self):
        assert flatten_docker_compose(self.setting, "DEBUG=1") == "DEBUG=1"

    def test_list_is_not_a_valid_value(self):
        with pytest.raises(
            ConfigError, match="must be an object of variable name to value"
        ):
            flatten_docker_compose(self.setting, ["DEBUG=1"])


class TestLoadSettingsFile:

    @pytest.mark.parametrize(
        ("name", "content"),
        [
            ("base.yaml", "jira:\n  project_key: PROJ\n"),
            ("base.yml", "jira:\n  project_key: PROJ\n"),
            ("base.json", '{"jira": {"project_key": "PROJ"}}'),
        ],
        ids=["yaml", "yml", "json"],
    )
    def test_file_is_loaded(self, write_config, name, content):
        assert load_settings_file(write_config(name, content)) == {
            "JIRA_PROJECT_KEY": "PROJ"
        }

    def test_empty_file_is_loaded_as_no_settings(self, write_config):
        assert load_settings_file(write_config("base.yaml", "")) == {}

    @pytest.mark.parametrize(
        ("name", "content"),
        [("base.yaml", "jira: [\n"), ("base.json", "{")],
        ids=["yaml", "json"],
    )
    def test_invalid_syntax_is_reported_with_the_file_name(
        self, write_config, name, content
    ):
        with pytest.raises(
            ConfigError, match='Invalid config file ".*{}"'.format(name)
        ):
            load_settings_file(write_config(name, content))

    def test_invalid_structure_is_reported_with_the_file_name(self, write_config):
        file = write_config("base.yaml", "aliases:\n  - project up\n")
        with pytest.raises(
            ConfigError, match='Invalid config file ".*base.yaml": setting "aliases"'
        ):
            load_settings_file(file)


class TestIterConfigFiles:

    def test_files_of_all_formats_are_returned_in_the_alphabetical_order(
        self, write_config, config_dir
    ):
        for name in ("prod.yml", "dev.json", "base.conf", "extra.yaml"):
            write_config(name, "")
        assert [file.name for file in iter_config_files(config_dir)] == [
            "base.conf",
            "dev.json",
            "extra.yaml",
            "prod.yml",
        ]

    def test_files_starting_with_tilde_are_skipped(self, write_config, config_dir):
        write_config("~prod.yaml", "")
        write_config("base.yaml", "")
        assert [file.name for file in iter_config_files(config_dir)] == ["base.yaml"]

    def test_files_with_an_unknown_suffix_are_skipped(self, write_config, config_dir):
        write_config("README.md", "")
        write_config("base.yaml", "")
        assert [file.name for file in iter_config_files(config_dir)] == ["base.yaml"]

    def test_directories_are_skipped(self, write_config, config_dir):
        (config_dir / "scripts.yaml").mkdir()
        write_config("base.yaml", "")
        assert [file.name for file in iter_config_files(config_dir)] == ["base.yaml"]

    def test_missing_config_dir_returns_no_files(self, config_dir):
        assert list(iter_config_files(config_dir / "missing")) == []


class TestLoadConfig:

    def test_settings_of_all_formats_are_loaded_into_the_environment(
        self, write_config, config_path
    ):
        write_config("base.yaml", "jira:\n  project_key: PROJ\n")
        write_config("dev.json", '{"jira": {"url": "https://jira.example.com"}}')
        write_config("extra.conf", "JIRA_USERNAME=user\n")

        load_config(config_paths=[config_path])

        assert os.environ["JIRA_PROJECT_KEY"] == "PROJ"
        assert os.environ["JIRA_URL"] == "https://jira.example.com"
        assert os.environ["JIRA_USERNAME"] == "user"

    def test_file_with_the_highest_order_overrides_the_previous_one(
        self, write_config, config_path
    ):
        write_config("base.yaml", "jira:\n  project_key: BASE\n")
        write_config("dev.conf", "JIRA_PROJECT_KEY=DEV\n")
        write_config("prod.yaml", "jira:\n  project_key: PROD\n")

        load_config(config_paths=[config_path])

        assert os.environ["JIRA_PROJECT_KEY"] == "PROD"

    def test_config_overrides_the_variable_set_in_the_environment(
        self, write_config, config_path, monkeypatch
    ):
        monkeypatch.setenv("JIRA_PROJECT_KEY", "ENV")
        write_config("base.yaml", "jira:\n  project_key: PROJ\n")

        load_config(config_paths=[config_path])

        assert os.environ["JIRA_PROJECT_KEY"] == "PROJ"

    def test_project_config_overrides_the_general_one(
        self, write_config, config_path, tmp_path
    ):
        general_path = tmp_path / "general"
        (general_path / ".pydev").mkdir(parents=True)
        (general_path / ".pydev" / "base.yaml").write_text(
            "jira:\n  project_key: GENERAL\n  url: https://jira.example.com\n"
        )
        write_config("base.yaml", "jira:\n  project_key: PROJECT\n")

        load_config(config_paths=[general_path, config_path])

        assert os.environ["JIRA_PROJECT_KEY"] == "PROJECT"
        assert os.environ["JIRA_URL"] == "https://jira.example.com"
