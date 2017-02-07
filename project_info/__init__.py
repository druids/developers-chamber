import os.path
import json


def get_project_info_dict(pip_config=None):
    if pip_config is None:
        from django.conf import settings

        pip_config = settings.PIP_CONFIG

    if os.path.isfile(pip_config):
        with open(pip_config) as pip_file:
            return json.load(pip_file)
    else:
        return {}


def get_version(pip_config=None):
    return get_project_info_dict(pip_config).get('version')
