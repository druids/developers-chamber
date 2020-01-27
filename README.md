Developers-chamber
==================

Library of helpers for python development.

Instalation
-----------

### Register plugin in requirements.txt and in you Django configuration

```python
pip install developers-chamber
```

## System libraries

### Docker

Docker and docker-compose is required for most of `pydev project` commands.


### Bindfs

Pydev command `pydev project bind-library` uses system library to mount directory with library to docker shared volume. 

Instalation command for linux/macOS:
```bash
apt-get install bindfs
yum install bindfs
brew install bindfs
```

Completion
----------

You can install bash completion with command

```bash
pydev init-completion
```

Commands
--------

For list of all commands you can run command:

```bash
pydev --help
```

### Bitbucket

Group of commands which contains helpers to create or update pull requests.

### Docker

List of helpers for docker and docker-compose.

### Git

Commands simplifying working with git and help with releasing.

### QA

Quality assurance commands.

### Version

Project versioning.

### Sh

Shell or bash scripts.

### ecs

AWS ESC commands.

### Jira

Jira helpers.

### Toggle

Time tracking helpers.

### Project

Group of commands which joins previous commands for simplifier development.
