import subprocess


def build(project_name, files, no_cache, container=None):
    compose_command = [
        'docker-compose',
        '-p{}'.format(project_name),
    ] + [
        '-f{}'.format(file) for file in files
    ]
    compose_command.append('build')

    if no_cache:
        compose_command.append('--no-cache')
    if container:
        compose_command.append(container)

    subprocess.run(compose_command)


def run_command(project_name, files, container, command):
    compose_command = [
        'docker-compose',
        '-p{}'.format(project_name),
    ] + [
        '-f{}'.format(file) for file in files
    ]
    compose_command.append('run')
    compose_command.append(container)
    compose_command.append(command)
    subprocess.run(compose_command)


def exec_command(project_name, files, container, command):
    compose_command = [
        'docker-compose',
        '-p{}'.format(project_name),
    ] + [
        '-f{}'.format(file) for file in files
    ]
    compose_command.append('exec')
    compose_command.append(container)
    compose_command.append(command)
    subprocess.run(compose_command)


def run_bash(project_name, files, container):
    run_bash(project_name, files, container, 'bash')


def exec_bash(project_name, files, container):
    exec_bash(project_name, files, container, 'bash')


def kill_all():
    subprocess.run('docker kill $(docker ps -qa)')


def clean_all():
    subprocess.run('docker image prune -f')
    subprocess.run('docker container prune -f')


def clean_all_hard():
    subprocess.run('docker system prune -af')
    subprocess.run('docker volume rm $(docker volume ls -q)')