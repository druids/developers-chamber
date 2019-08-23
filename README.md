Developers-chamber
==================

A small plugin which takes a configuration (like Bower or npm) and it provides data via context processors.

Usage
-----

### Register plugin in requirements.txt and in you Django configuration

```python
pip install developers-chamber
```

and

```python
TEMPLATE_CONTEXT_PROCESSORS = (
    'developers_chamber.django.context_processors.get_project_info',
)

PIP_CONFIG = 'version.json'
```

### Create a pip.json (the name depends on you, but must be same in Django configuration)

```json
{
    "name": "short project name",
    "version": "0.1.0",
    "verbose": "verbose project name"
}
```

### Templates

All values from `version.json` are available in a template via the context processor. Every key is capitalized and prefixed by PROJECT_, e.g. version becomes PROJECT_VERSION.

### Helpers

There are several helpers for development and releasing, you can use it as scripts:

* release-bitbucket - support creating bitbucket pull-requests
* release-git - helpers for creating release/deployment branches
* release-version - helpers for changing project version

more informations you will obtain with `--help`:

```bash
release-bitbucket --help
release-git --help
release-version --help
```