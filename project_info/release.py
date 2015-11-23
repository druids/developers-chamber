from __future__ import print_function

import json
import os.path
import git
import re
import sys


RELEASE_TYPES = ('major', 'minor', 'patch')

VERSION_RE = re.compile('"version": "[0-9][0-9]*\.[0-9][0-9]*(\.)?([0-9][0-9]*)?"')


def inc(num):
    return num + 1


def zero(num):
    return 0


def iden(num):
    return num


VERSION_DELTA = {
    'major': (inc, zero, zero),
    'minor': (iden, inc, zero),
    'patch': (iden, iden, inc),
}


def make_collection(string_or_tuple):
    return (string_or_tuple,) if isinstance(string_or_tuple, str) else string_or_tuple


def error(msg):
    [print(message, file=sys.stderr) for message in make_collection(msg)]


def info(msg):
    [print(message, file=sys.stdout) for message in make_collection(msg)]


def write_version(project_dir, f, substitution, str_version):
    try:
        handler = open(os.path.join(project_dir, f), 'r+')
        replaced = VERSION_RE.sub(substitution, handler.read())
        handler.seek(0)
        handler.write(replaced)
        handler.close()
        return ('Version bumped to {} (in {})'.format(str_version, f), None)
    except IOError as e:
        return (None, 'An error occurred: {}'.format(e))


def compose_version(release_type, current_version):
    version_func = VERSION_DELTA[release_type] if release_type in VERSION_DELTA else VERSION_DELTA['patch']
    return (func(current_version[i]) for i, func in enumerate(version_func))


def merge_branch(git_cmd, g, branch, no_ff_commit, release_branch, origin):
    g.checkout(branch)
    git_cmd.execute(('git', 'merge', '--no-ff', '-m', no_ff_commit, release_branch))
    g.push(origin, branch)
    return ('{} to {}'.format(no_ff_commit, branch), 'Pushed {} to origin'.format(branch))


def compact(seq):
    return tuple(item for item in seq if item is not None)


def release(project_dir, release_type='patch', files=['pip.json'], next_branch='next', origin='origin'):

    if release_type not in RELEASE_TYPES:
        error('An invalid release type given: {} \nExpected: {}'.format(release_type, ', '.join(RELEASE_TYPES)))
        return 1

    if len('files') is 0:
        error('Given no files to release a version')
        return 2

    # GitPython does not support merge --no-ff or what?
    git_cmd = git.cmd.Git(project_dir)

    repo = git.Repo(project_dir)
    g = repo.git

    g.checkout(next_branch)

    current_version = '0.1.0'
    any_config = os.path.join(project_dir, files[0])
    if any_config and os.path.isfile(any_config):
        handler = open(any_config)
        json_data = json.load(handler)
        current_version = json_data['version'] or current_version
        handler.close()

    tokens = current_version.split('.')
    if not len(tokens) is 3:
        error('An invalid version format given: {}'.format(current_version))
        return 3

    version = compose_version(release_type, tuple(map(int, tokens)))
    str_version = '.'.join(str(item) for item in version)
    g.pull(origin, next_branch)

    release_branch = "release-" + str_version
    g.checkout(next_branch, b=release_branch)

    substitution = '"version": "{}"'.format(str_version)
    infos, errors = tuple(compact(msgs)
                          for msgs in tuple(zip(*tuple(write_version(project_dir, f, substitution, str_version)
                                                       for f in files))))
    if len(errors):
        [error(err) for err in errors]
        return 4

    [info(msg) for msg in infos]

    g.add(files)
    g.commit(m=str_version)
    info('Committed as "{}"'.format(str_version))
    g.tag(str_version)
    info('Tagged as "{}"'.format(str_version))

    g.push(origin, release_branch)

    no_ff_commit = "Merge branch 'release-{}'".format(str_version)
    for msg in (merge_branch(git_cmd, g, branch, no_ff_commit, release_branch, origin)
                for branch in ('master', next_branch)):
        info(msg)

    git_cmd.execute(('git', 'push', origin, '--tags'))

    return 0
