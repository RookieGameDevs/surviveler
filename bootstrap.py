#!/usr/bin/env python
"""Surviveler bootstrap script.

This script eases the project setup for development and running. It takes care
of downloading needed dependencies and building them locally.
"""
import os
import stat
import subprocess as sp
import sys


BUILD_DIR = 'build'


def waf_is_configured(path):
    return os.path.exists(os.path.join(path, 'build'))


def waf_configure(path, options):
    return sp.run(['./waf', 'configure'] + options.split(), cwd=path)


def waf_build_and_install(path):
    return sp.run(['./waf', 'build', 'install'], cwd=path)


def build_datalib(name, path):
    if not waf_is_configured(path):
        proc = waf_configure(path, '--prefix=../')
        if proc.returncode != 0:
            return proc.returncode, proc.stderr.decode('utf8')
    proc = waf_build_and_install(path)
    if proc.returncode != 0:
        return proc.returncode, proc.stderr.decode('utf8')
    return 0, ''


def build_renderlib(name, path):
    if not waf_is_configured(path):
        inst_path = os.path.abspath(os.path.join(path, '..'))
        proc = waf_configure(
            path,
            '--prefix=../ --datalib-path={} --matlib-path={}'.format(
                inst_path,
                inst_path))
        if proc.returncode != 0:
            return proc.returncode, proc.stderr.decode('utf8')
    proc = waf_build_and_install(path)
    if proc.returncode != 0:
        return proc.returncode, proc.stderr.decode('utf8')
    return 0, ''


def build_matlib(name, path):
    if not waf_is_configured(path):
        proc = waf_configure(path, '--prefix=../')
        if proc.returncode != 0:
            return proc.returncode, proc.stderr.decode('utf8')
    proc = waf_build_and_install(path)
    if proc.returncode != 0:
        return proc.returncode, proc.stderr.decode('utf8')
    return 0, ''


TARGETS = [
    {
        'name': 'datalib',
        'url': 'git@github.com:RookieGameDevs/datalib.git',
        'ref': 'b7ad087aef26e5d3dda3d6021e03ba1d43a8871d',
        'build': build_datalib,
    },
    {
        'name': 'matlib',
        'url': 'git@github.com:RookieGameDevs/matlib.git',
        'ref': 'ac5d3489442a0e82571d441b94c7212dc68b6a43',
        'build': build_matlib,
    },
    {
        'name': 'renderlib',
        'url': 'git@github.com:RookieGameDevs/renderlib.git',
        'ref': 'b4b8eb77158d8785260663448d2ccc46531d5ba9',
        'build': build_renderlib,
    },
]


class InvalidGitRepo(Exception):
    """Invalid Git repository."""
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return 'Invalid Git repository {}'.format(self.path)


def git_cmd(cmd, path):
    return sp.run(['git'] + cmd.split(), stdout=sp.PIPE, stderr=sp.PIPE, cwd=path)


def git_check_repo(path):
    if not os.path.exists(os.path.join(path, '.git')) or git_cmd('status', path).returncode != 0:
        return False
    return True


def git_get_head(path):
    if not git_check_repo(path):
        raise InvalidGitRepo(path)


def git_checkout(ref, path):
    if not git_check_repo(path):
        raise InvalidGitRepo(path)

    checkout_cmd = 'checkout {}'.format(ref)

    # try to checkout the given ref
    proc = git_cmd(checkout_cmd, path)
    if proc.returncode != 0:
        # attempt to fetch from all remotes
        proc = git_cmd('fetch --all', path)
        if proc.returncode == 0:
            proc = git_cmd(checkout_cmd, path)

    return proc.returncode, proc.stderr.decode('utf8')


def clone_or_checkout(url, ref, path):
    # if the path does not exist, try to clone the repository
    if not os.path.exists(path):
        proc = sp.run(['git', 'clone', url, path])
        if proc.returncode != 0:
            return proc.returncode, proc.stderr.decode('utf8')

    try:
        return git_checkout(ref, path)
    except InvalidGitRepo as err:
        return 1, '{}'.format(err)


def pip_install(python_path, inst_path):
    inst_path = os.path.abspath(inst_path)
    env = dict(os.environ)
    env.update({
        'CFLAGS': '-I{inst_path}/include -I{inst_path}/include/renderlib'.format(inst_path=inst_path),
        'LDFLAGS': '-L{inst_path}/lib'.format(inst_path=inst_path),
    })
    proc = sp.run(
        [python_path, '-m', 'pip', 'install', '-r', 'requirements.txt'],
        env=env)
    return proc.returncode, proc.stderr.decode('utf8') if proc.returncode else ''


def venv_setup(venv_path, inst_path):
    proc = sp.run([sys.executable, '-m', 'venv', venv_path])
    if proc.returncode != 0:
        return proc.returncode, proc.stderr.decode('utf8')

    launcher_tmpl = (
        '#!/bin/sh\n'
        'LD_LIBRARY_PATH={library_path} {python_path} src/client/main.py "$@"'
    ).format(
        library_path=os.path.abspath(os.path.join(inst_path, 'lib')),
        python_path=os.path.abspath(os.path.join(venv_path, 'bin', 'python')))

    launcher_path = os.path.join(venv_path, 'bin', 'client')
    with open(launcher_path, 'w') as fp:
        fp.write(launcher_tmpl)

    st = os.stat(launcher_path)
    os.chmod(launcher_path, st.st_mode | stat.S_IEXEC)

    return 0, ''


def server_install(root_path):
    env = dict(os.environ)
    env['GOPATH'] = os.path.abspath(root_path)
    proc = sp.run(['go', 'install', 'server'], env=env)
    return proc.returncode, proc.stderr.decode('utf8') if proc.returncode else ''


if __name__ == '__main__':
    # setup virtualenv
    venv_path = os.getcwd()
    python_path = os.path.join(venv_path, 'bin', 'python')
    if not os.path.exists(venv_path) or not os.path.exists(python_path):
        returncode, error = venv_setup(venv_path, BUILD_DIR)
        if returncode != 0:
            print('Failed to setup virtualenv: {}'.format(error))

    # create build directory, if it doesn't exist
    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)

    # clone targets
    for tgt in TARGETS:
        returncode, error = clone_or_checkout(
            tgt['url'],
            tgt['ref'],
            os.path.join(BUILD_DIR, tgt['name']))
        if returncode != 0:
            print('Failed to checkout "{}": {}'.format(tgt['name'], error))
            exit(returncode)

    # build targets
    for tgt in TARGETS:
        returncode, error = tgt['build'](tgt['name'], os.path.join(BUILD_DIR, tgt['name']))
        if returncode != 0:
            print('Failed to build "{}": {}'.format(tgt['name'], error))
            exit(returncode)

    # install packages via PIP
    returncode, error = pip_install(python_path, BUILD_DIR)
    if returncode != 0:
        print('Failed to install packages via PIP: {}'.format(error))

    # build server
    returncode, error = server_install(os.getcwd())
    if returncode != 0:
        print('Failed to install server: {}'.format(error))
