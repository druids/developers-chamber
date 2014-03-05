import json
import os.path
import git
import re


RELEASE_TYPES = ('major', 'minor', 'patch')


def release(project_dir, release_type='patch', files=['pip.json'], next_branch='next', origin='origin'):

    if not release_type in RELEASE_TYPES:
        info = release_type, ', '.join(RELEASE_TYPES)
        print 'An invalid release type given: %s \nExpected: %s' % info
        return 1

    if len('files') is 0:
        print 'Given no files to release a version'
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
        print 'An invalid version format given: %' % current_version
        return 3

    version = map(int, tokens)

    if release_type == 'patch':
        version[2] += 1
    elif release_type == 'minor':
        version[1] += 1
        version[2] = 0
    else:
        version[0] += 1
        version[1] = 0
        version[2] = 0

    str_version = '.'.join(str(item) for item in version)
    g.pull(origin, next_branch)

    release_branch = "release-" + str_version
    g.checkout(next_branch, b=release_branch)

    regexp = re.compile('"version": "[0-9][0-9]*\.[0-9][0-9]*(\.)?([0-9][0-9]*)?"')
    substitution = '"version": "%s"' % str_version
    for f in files:
        try:
            handler = open(os.path.join(project_dir, f), 'r+')
            replaced = regexp.sub(substitution, handler.read())
            handler.seek(0)
            handler.write(replaced)
            handler.close()
        except IOError, e:
            print 'An error occurred: %s' % e
            return 4

    g.add(files)
    g.commit(m=str_version)
    g.tag(str_version)

    g.push(origin, release_branch)

    no_ff_commit = "Merge branch 'release-%s'" % str_version
    for branch in ('master', next_branch):
        g.checkout(branch)
        git_cmd.execute(('git', 'merge', '--no-ff', '-m', no_ff_commit, release_branch))
        g.push(origin, branch)

    git_cmd.execute(('git', 'push', origin, '--tags'))

    return 0
