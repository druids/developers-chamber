import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from developers_chamber.click.options import (
    ContainerCommandType,
    ContainerDirToCopyType,
    ContainerEnvironment,
)

CONFIG_DIR_NAME = ".pydev"
DOTENV_SUFFIXES = (".conf",)
JSON_SUFFIXES = (".json",)
YAML_SUFFIXES = (".yaml", ".yml")
STRUCTURED_SUFFIXES = JSON_SUFFIXES + YAML_SUFFIXES


class ConfigError(Exception):
    """Raised when a configuration file cannot be read or has an invalid structure."""


def _format_path(path):
    return ".".join(path) if path else "<root>"


def _fail(path, message):
    raise ConfigError('setting "{}": {}'.format(_format_path(path), message))


def _encode_scalar(value, path):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value)
    _fail(path, "unsupported value type {}".format(type(value).__name__))


def _encode_value(value, path):
    """Encode a value which has no dedicated encoder into its environment variable form."""
    if isinstance(value, (list, tuple)):
        return ",".join(_encode_scalar(item, path) for item in value)
    return _encode_scalar(value, path)


def _encode_aliases(value, path):
    """
    ALIASES is read with ``json.loads`` in ``developers_chamber.scripts.init_aliasses``.

    Only the shape of the whole setting is checked here, the accepted form of a single alias
    is validated by ``AliasCommand`` which is the one that knows it.
    """
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        _fail(path, "must be an object of alias name to command")
    return json.dumps(value)


def _param_type_encoder(param_type):
    """
    Build an encoder delegating to the param type which parses the setting back.

    The param type returns either the whole value of the setting or its items which are then
    joined by the common list separator.
    """

    def encode(value, path):
        try:
            return _encode_value(param_type.encode(value), path)
        except ValueError as ex:
            _fail(path, str(ex))

    return encode


# Settings which are not plain scalars or comma separated lists. The key is the resulting
# environment variable name, the value is a callable turning the structured value into the
# string form expected by the command which reads it. Every encoder also accepts the string
# form itself, so the flat notation keeps working in the structured config files too.
SETTING_ENCODERS = {
    "ALIASES": _encode_aliases,
    "PROJECT_DOCKER_COMPOSE_CONTAINERS_DIR_TO_COPY": _param_type_encoder(
        ContainerDirToCopyType
    ),
    "PROJECT_DOCKER_COMPOSE_CONTAINERS_INSTALL_COMMAND": _param_type_encoder(
        ContainerCommandType
    ),
    "PROJECT_DOCKER_COMPOSE_CONTAINERS_ENV": _param_type_encoder(ContainerEnvironment),
}


def _flatten(data, name_parts, path, result):
    for key, value in data.items():
        name_parts_of_key = name_parts + (str(key).replace("-", "_").upper(),)
        name = "_".join(name_parts_of_key)
        key_path = path + (str(key),)

        if value is None:
            continue

        encoder = SETTING_ENCODERS.get(name)
        if encoder is not None:
            result[name] = encoder(value, key_path)
        elif isinstance(value, dict):
            _flatten(value, name_parts_of_key, key_path, result)
        else:
            result[name] = _encode_value(value, key_path)
    return result


def flatten_settings(data):
    """
    Turn a structured configuration into the environment variables which the pydev commands read.

    Nested objects are sections joined with an underscore (``jira.project_key`` becomes
    ``JIRA_PROJECT_KEY``), lists are joined with a comma and ``None`` values are left out.
    Settings listed in ``SETTING_ENCODERS`` are encoded by their own rules.
    """
    if not isinstance(data, dict):
        _fail((), "root element must be an object")
    return _flatten(data, (), (), {})


def load_settings_file(file):
    """Read a single JSON or YAML configuration file and return its environment variables."""
    file = Path(file)
    try:
        with file.open() as f:
            if file.suffix in JSON_SUFFIXES:
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
    except (json.JSONDecodeError, yaml.YAMLError) as ex:
        raise ConfigError('Invalid config file "{}": {}'.format(file, ex))

    if data is None:
        return {}

    try:
        return flatten_settings(data)
    except ConfigError as ex:
        raise ConfigError('Invalid config file "{}": {}'.format(file, ex))


def iter_config_files(config_dir):
    """Yield enabled configuration files of the directory in the order in which they are applied."""
    if not config_dir.is_dir():
        return
    for file in sorted(config_dir.iterdir()):
        if not file.is_file() or file.name.startswith("~"):
            continue
        if file.suffix in DOTENV_SUFFIXES + STRUCTURED_SUFFIXES:
            yield file


def load_config(config_paths=None):
    """
    Load the pydev configuration into the environment variables.

    The general configuration in the home directory is loaded first and the project one in the
    current directory second, therefore the project configuration wins. Inside a directory the
    files are applied in the alphabetical order no matter their format.
    """
    if config_paths is None:
        config_paths = (Path.home(), Path.cwd())

    for config_path in config_paths:
        for file in iter_config_files(Path(config_path) / CONFIG_DIR_NAME):
            if file.suffix in DOTENV_SUFFIXES:
                load_dotenv(dotenv_path=str(file), override=True)
            else:
                os.environ.update(load_settings_file(file))
