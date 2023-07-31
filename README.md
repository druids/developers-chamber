# Developers-chamber

Library of helpers for python development.

# Installation

## Register plugin in requirements.txt and in you Django configuration

```python
pip install developers-chamber
```

## Required system libraries

### Docker

Docker and docker-compose is required for most of `pydev project` commands.

### Bindfs

If you want to use pydev command `pydev project bind-library` you have to install `bindfs` for mounting location to the right directory. For exymple you can mount directory with library to a docker shared volume. 

Instalation command for linux/macOS:
```bash
apt-get install bindfs
yum install bindfs
brew install bindfs
```

## Bash completion

You can install a bash completion with pydev command `init-completion`:

```bash
pydev init-completion
```

## Configuration files

You can configure pydev for your project with config files. You can define more config files which is loaded with alphabetical order (file with the highest order will override the same configuration with the lowest order).
There are two places for the pydev configuration files. One place is used for all the projects and the second one is project specific. 
The purpose of the general pydev settings is to have some place where you can store your personal or secret configuration for example key to your personal toggle account. The directory for general settings is `$HOME/.pydev`.
The project configuration directory is stored in path `$PROJECT_DIR/.pydev` and works only if pydev commands are run in the `$PROJECT_DIR` directory. The same values in the general configuration will be overriden by to project configuration. 


Configuration files which are stored in the `.pydev` directory must have this format:
```bash
./.pydev/
    base.conf
    dev.conf
    prod.conf
```

If you want to disable configuration file you can rename it to start with character `~`. In the example `~prod.conf` will be ignored:

```bash
./.pydev/
    base.conf
    dev.conf
    ~prod.conf
```

The configuration file may contain project settings and aliases.

### Settings

Project settings saves the time to the developers because pydev input parameters may be omitted if the parameter is defined in the configuration file. Example of such file can be:

JIRA_PROJECT_KEY=PROJ
PROJECT_DOCKER_COMPOSE_FILES=path/to/the/compose.yaml
PROJECT_DOCKER_COMPOSE_DEFAULT_UP_CONTAINERS=container_a,container_b
PROJECT_DOCKER_COMPOSE_CONTAINERS_DIR_TO_COPY=container_a:/usr/local/lib/python3.11/site-packages:var/site-packages
PROJECT_DOCKER_COMPOSE_CONTAINERS_INSTALL_COMMAND=base:./manage.py compilemessages && ./manage.py migrate && ./manage.py collectstatic
PROJECT_DOCKER_COMPOSE_VAR_DIRS=var,var/data/media,var/data/static
PROJECT_LIBRARY_DIR=var/site-packages

### Alias

Alias is a shortcut for the developer to save his time and are defined with `ALIASES` setting in a JSON format:

```bash
ALIASES='{
    "up": "project up",
    "up-all": "project up -a",
}'
```

You can now use aliases to run pydev commands:

```bash
pydev up     # instead of pydev project up
pydev up-all # instead of pydev project up -a
```

You can write alias with arguments too:

```bash
ALIASES='{
    "migrate": "project run \"python manage.py migrate $app\"",
}'
```

You can now run migration to the concrete app with:

```bash
pydev migrate --app=users # it will run pydev project run "python manage.py migrate users"
```

There can be situations when you need to alias on more commands. You can use JSON list to specify it:

```bash
ALIASES='{
    "build-js": ["project run -c static \"build-js.sh\"", "project run -c base \"./manage.py collectstatic\""],
}'
```

Now you can run only one pydev command to build js and collect django static files:

```bash
pydev buildjs
```

Everything what you define after pydev alias will be sent into the command:

```bash
ALIASES='{
    "run-dj": "project run \"./manage.py\"",
}'

# bash
pydev run-dj migrate --no-input
```

Will run `./manage.py migrate --no-input` on the docker instance.

# Commands

For list of all commands you can run command:

```bash
pydev --help
```

### Bitbucket

Group of commands or helpers which provides manage pull requests in the Bitbucket service.

#### Commands
* `pydev bitbucket create-release-pull-request` - create a new pull request to the bitbucket repository

#### Configuration
* `BITBUCKET_USERNAME` - username fo the Bitbucket service
* `BITBUCKET_PASSWORD` - password to the Bitbucket service
* `BITBUCKET_BRANCH_NAME` - pull request destination branch name
* `BITBUCKET_REPOSITORY` - name of the destination repository

### Docker

Docker utilities helping with managing docker in your project:

#### Commands
* `pydev docker login` - login to the docker registry
* `pydev docker tag` - tag a docker image
* `pydev docker push-image` - push image to the docker repository

### Git

Helpers to run git commands which simplify releasing.

#### Commands
* `pydev git create-release-branch` - create a release branch and push it to the remote repository if the remote name is specified
* `pydev git create-deployment-branch` - create a deployment branch and new commit to trigger a deployment event
* `pydev git checkout-to-release-branch` - checkout git repository back to the release branch from deployment branch
* `pydev git bump-version-from-release-branch` - get version defined in the release branch and bump version files
* `pydev git commit-version` - commit version files and add git tag to the commit
* `pydev git merge-release-branch` - merge current branch to the selected branch
* `pydev git init-hooks` - initialize git hooks defined in the directory ./.pydev/git/hooks

#### Configuration
* `GIT_REMOTE_NAME` - remote repository name
* `GIT_BRANCH_NAME` - source branch name for create-release-branch command

### Gitlab

Helpers for GitLab management.

#### Commands
* `pydev git create-release-merge-request` - create a new merge request in a GitLab project. It is often used after the project release

#### Configuration
* `GITLAB_API_URL` - URL to gitlab API service
* `GITLAB_PROJECT` - GitLab project name
* `GITLAB_TARGET_BRANCH` - target branch for the merge request
* `GITLAB_TOKEN` - GitLab authentication token

### QA

Helpers for python project quality assurance.

#### Commands
* `pydev qa all` - run all QA checks
* `pydev qa missing-migrations` - run a missing Django migrations QA check. It will try to generate a Django migrations if there is one or more missing check is failed
* `pydev qa migration-filenames` - run migration filenames QA check. Migration name should be in format "[0-9]{4}_migration.py" (ex. 0001_migration.py)
* `pydev qa missing-translations` - run missing translations QA check. It will try to generate a Django `makemessages` if there is one or more missing check is failed
* `pydev qa import-order` - run import order QA check. It will check if all the new python code imports have the right order defined with isort command
* `pydev qa test-method-names` - runs test method names QA check. It will check if the new test methods has the right name in format defined in `QA_DISALLOWED_TEST_METHOD_REGEXP` setting

#### Configuration
* `QA_DISALLOWED_TEST_METHOD_REGEXP` - your disallowed test method regex. Example: `"def (test_should_[^\(]+)\("` 

### Version

Helpers for automatic update version in the version file.

#### Commands
* `pydev version bump-to-next` - bump version in the JSON file (or files) and print it
* `pydev version print-version` - return current project version according to version JSON file
* `pydev version print-next` - return next version according to input release type, build hash and version JSON file

#### Configuration
* `VERSION_FILES` - path to the files containing information about project version. There can be more paths which are split with character `,`.

### Sh

You can run shell commands with this utility:

* `pydev sh ls` 

The utility can be used in the `ALIASES`.

### ecs

Helpers for AWS ECS management.

#### Commands
* `pydev ecs deploy-new-task-definition` - deploy new task definition in AWS ECS. This command also updates the service and forces new deployment
* `pydev ecs register-new-task-definition` - register new task definition in AWS ECS
* `pydev ecs update-service-to-latest-task-definition` - update service with the latest available task_definition
* `pydev ecs stop-service` - stop an AWS ECS service by updating its desiredCount to 0
* `pydev ecs start-service` - start an AWS ECS service by updating its desiredCount to 0
* `pydev ecs start-cluster-services` - start an AWS ECS service by updating its desiredCount to 0
* `pydev ecs start-services` - start an AWS ECS service by updating its desiredCount to 0
* `pydev ecs run-task` - run a single task in AWS ECS
* `pydev ecs run-task-and-wait-for-success` - run a single task in AWS ECS and wait for it to stop with success
* `pydev ecs run-service-task` - run a single task based on service's task definition in AWS ECS and wait for it to stop with success
* `pydev ecs run-service-task-fargate` - run a single task based on service's task definition in AWS ECS and wait for it to stop with success
* `pydev ecs get-tasks-for-service` - return list of tasks running under specified service
* `pydev ecs get-task-definition-for-service` - return task definition arn for specified service
* `pydev ecs stop-service-and-wait-for-tasks-to-stop` - stop service and wait for the tasks to stop
* `pydev ecs stop-services-and-wait-for-tasks-to-stop` - stop services and wait for the tasks to stop
* `pydev ecs get-services-names` - get names of the cluster services
* `pydev ecs redeploy-services` - redeploy services by forcing new service deployment
* `pydev ecs redeploy-cluster-services` - redeploy all cluster services by forcing new service deployment
* `pydev ecs wait-for-services-stable` - wait until all non-daemon services in cluster are stable

#### Configuration
* `AWS_REGION` - your AWS region
* `AWS_ECS_CLUSTER` - name of your AWS ECS cluster

### Jira

Helpers for Jira management.

#### Commands
* `pydev git my-issues` - list issue of the current user according to JQL query
* `pydev git get-branch-name` - generates a new branch name according to the Jira issue
* `pydev git show-issue` - open an issue with the key in a web browser
* `pydev git log-issue-time` - log a spend time to the issue in the Jira worklog
* `pydev git print-issue-worklog` - print Jira issue worklog
* `pydev git invoke-issues-transition` - invoke Jira transition defined with transition name which may change Jira issues status.

#### Configuration
* `JIRA_URL` - URL to the Jira application
* `JIRA_USERNAME` - Username for access to the Jira
* `JIRA_API_KEY` - API key to the Jira
* `JIRA_JQL` - JQL for issue listing. Defaut value is:
```JQL
'project = {project_key} and assignee = currentUser() and status not in ("Done", "Canceled", "Closed") and sprint != null order by created DESC'
```
* `JIRA_PROJECT_KEY` - key of the project in the Jira

### Toggle

Helpers for time tracking with toggle service.

#### Commands
* `pydev toggle start` - start the Toggle timer with description in workspace ID and project ID
* `pydev toggle stop` - stops currently running the Toggl timer
* `pydev toggle print-toggl` - print detail of the currently running Toggle timer
* `pydev toggle print-report` - print summary from the Toggle time tracker. Data can be filtered according to workspace, project, description or by date and time
* `pydev toggle print-report-tasks` - print tracked the Toggle tasks one by one in table. Data can be filtered according to workspace, project, description or by date and time

#### Configuration
* `TOGGL_API_KEY` - the Toggle access API key
* `TOGGL_PROJECT_ID` - the Toggle project identifier
* `TOGGL_WORKSPACE_ID` - the Toggle workspace ID

### Project

Group of commands which joins previous commands for simplifier development.

#### Commands
* `pydev project set-domain` - set local hostname translation to localhost. It updates `/etc/hosts` headers according to input domain
* `pydev project build` - build docker container via compose file and name it with the project name
* `pydev project run` - run one time command on docker container defined in compose file. You can specify image environment variables
* `pydev project exec-command` - run command on already executed docker container defined in compose file
* `pydev project up` - builds, (re)creates, starts, and attaches to containers for a service defined in compose file
* `pydev project stop` - stop all the docker containers from the compose file
* `pydev project install` - builds, (re)creates, starts, and attaches to containers for a service defined in compose file
* `pydev project copy-container-dirs` - copy directories from a docker image to the host
* `pydev project bind-library` - mount a directory to an another location on docker host with bindfs
* `pydev project kill-all` - kill all running docker instances
* `pydev project clean` - clean docker images and its volumes. If you want to clean all the images and volumes use parameter -a
* `pydev project task start` - get information from Jira about issue and start Toggle timer
* `pydev project task stop` - stop Toggle timer and logs time to the Jira issue
* `pydev project task create-branch-from-issue` - create a new git branch from the source branch with name generated from the Jira issue
* `pydev project task create-or-update-pull-request` - create a Bitbucket pull request named according to the Jira issue
* `pydev project task sync-timer-log-to-issues` - synchronize logged time in Toggle timer with issues worklog in Jira
* `pydev project task print-last-commit-build` - print the last commit test results in Bitbucket of the selected branch

#### Configuration
* `PROJECT_DOCKER_COMPOSE_PROJECT_NAME` - project name which be used as a prefix aff all builded docker images with compose
* `PROJECT_DOCKER_COMPOSE_FILES` - list of the paths to the compose files separated by a character `,`
* `PROJECT_DOMAINS` - list of the project domain names separated by a character `,`
* `PROJECT_DOCKER_COMPOSE_CONTAINERS` - list of all your docker container names separated by a character `,`
* `PROJECT_DOCKER_COMPOSE_DEFAULT_UP_CONTAINERS` - list of docker container names separated by a character `,` which will be by default started with command `pydev project up`
* `PROJECT_DOCKER_COMPOSE_VAR_DIRS` - list of your variable directories which will be created before project build
* `PROJECT_DOCKER_COMPOSE_CONTAINERS_DIR_TO_COPY` - container dir which will be copied after build in format `DOCKER_CONTAINER_NAME:CONTAINER_DIRECTORY:HOST_DIRECTORY`
* `PROJECT_DOCKER_COMPOSE_CONTAINERS_INSTALL_COMMAND` - install that will be triggered after project build
* `PROJECT_LIBRARY_DIR` - the project library directory path on the docker host
* `PROJECT_SOURCE_BRANCH_NAME` - your project source branch name. By default value is set to `next`

### Slack

Anything what you need to send to Slack.

#### Commands
* `pydev slack upload-new-migrations` - send all new Django migration files between releases etc. to Slack

#### Configuration
* `SLACK_BOT_TOKEN` - Token to connect Slack. The [link](https://github.com/slackapi/python-slack-sdk/blob/main/tutorial/01-creating-the-slack-app.md) how to obtain the token.
