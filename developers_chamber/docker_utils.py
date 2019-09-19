from developers_chamber.utils import call_command


def login_client(username, password, registry):
    call_command(['docker', 'login', '--username', username, '--password', password, registry])


def tag(source_image, target_image):
    call_command(['docker', 'tag', source_image, target_image])


def push_image(repository, tag):
    call_command(['docker', 'push', '{}:{}'.format(repository, tag)])
