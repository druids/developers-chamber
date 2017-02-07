django-project-info
===================

A small plugin which takes a configuration (like Bower or npm) and it provides data via context processors.

Usage
-----

### Register plugin in requirements.txt and in you Django configuration

```python
https://github.com/lukasrychtecky/django-project-info/tarball/0.1.0#egg=django-project-info-0.1.0
```

and

```python
TEMPLATE_CONTEXT_PROCESSORS = (
    'project_info.context_processors.get_project_info',
)

PIP_CONFIG = 'pip.json'
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

All values from `pip.json` are available in a template via the context processor. Every key is capitalized and prefixed by PROJECT_, e.g. version becomes PROJECT_VERSION.

### Helpers

If you want to get only parsed pip.json file you can use get_project_info_dict

```python
from project_info import get_project_info_dict

get_project_info_dict()
```

You can specify pip config file

```python
get_project_info_dict('pip.json')
```

If you want to get only project version use

```python
from project_info import get_version

get_version()
```

again first parameter can be pip config file

```python
get_version('pip.json')
```