"""
Configuration agent for liquid-core

This module does daemonization voodoo. Its only public function, `launch`,
expects a `target_configuration` (the configuration that will be applied), and
returns a job object.

The job object has the following members:

* `id` - job identifier (an ISO UTC timestamp)
* `is_finished()` - checks if the job is done
* `open_logfile()` - opens the job's log file

Internally, the agent follows this script:

* Launch a python subprocess on this module.
* In the subprocess, daemonize.
* In the daemon, open the log file for "append".
* In the daemon, launch a python subprocess on this module, with stdout and
  stderr redirected to the log file.
* _That_ subprocess acquires a global lock, to ensure no other agents run at
  the same time.
* It then proceeds to apply the update - it modifies setup's configuration file
  and runs ansible.

"""

import time
import sys
import os
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import fcntl
import subprocess
import json
import yaml
import daemon


def launch(target_configuration):
    """ Launch a job to apply `target_configuration`. """
    from django.conf import settings

    var = Path(settings.LIQUID_CORE_VAR)
    setup = Path(settings.LIQUID_SETUP_DIR)

    task_data = {
        'target_configuration': target_configuration,
    }

    job = Job(timestamp(), var)
    with job.options_file.open('w', encoding='utf8') as f:
        print(json.dumps(task_data, indent=2), file=f)

    call_self_in_subprocess('daemonize', job.id, var, setup)

    return job


def timestamp():
    return str(datetime.utcnow().isoformat())


class Job:

    """
    A configuration job. This class does not encapsulate any configuration
    logic, only the job's metadata.
    """

    def __init__(self, id, var):
        self.id = id
        self.var = Path(var)

    @property
    def options_file(self):
        return self.var / 'job-{}.json'.format(self.id)

    def wait(self):
        print('Waiting for job {} to finish ...'.format(self.id))
        while self.task_file.exists():
            time.sleep(.2)

        print('Job {} done!'.format(self.id))

        with self.open_logfile() as f:
            print('================')
            print(f.read())
            print('================')

        return True

    def open_logfile(self, mode='r'):
        logs = self.var / 'logs'
        logs.mkdir(mode=0o755, exist_ok=True)
        logfile = logs / 'agent-{}.log'.format(self.id)
        if mode == 'r' and not logfile.exists():
            logfile.touch()
        return logfile.open(mode, encoding='utf8')


@contextmanager
def lock(path):
    with open(str(path), 'w') as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def call_self_in_subprocess(*args, **kwargs):
    argv = [sys.executable, __file__] + [str(a) for a in args]
    subprocess.run(argv, check=True, **kwargs)


def log(*args):
    print(*args, timestamp())


def run_shell(cmd, **kwargs):
    log('+', cmd)
    return subprocess.run(cmd, shell=True, **kwargs)


class State:

    """
    Read and write global state from disk. Only write to disk while holding the
    `agent.lock` lockfile.
    """

    def __init__(self, var):
        self.var = var
        self.state_file = var / 'state.json'
        self.new_state_file = var / 'new-state.json'

    def load(self):
        try:
            with self.state_file.open(encoding='utf8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save(self, state):
        with self.new_state_file.open('w', encoding='utf8') as f:
            print(json.dumps(state, indent=2, sort_keys=True), file=f)
        self.new_state_file.rename(self.state_file)

    def patch(self, **delta):
        self.save(dict(self.load(), **delta))


def do_the_job(job_id, var, setup):
    """
    Perform useful work, since by now we're in our own little world, with
    stdout+stderr redirected to the log file.
    """
    job = Job(job_id, var)
    state_db = State(var)
    log("Acquiring agent lock")
    with lock(var / 'agent.lock'):
        log("Acquired lock")
        if state_db.load().get('job'):
            raise RuntimeError("Another job was running and did not finish")
        state_db.patch(job=job_id)

        config_yml = setup / 'ansible' / 'vars' / 'config.yml'
        with config_yml.open(encoding='utf8') as g:
            old_config = yaml.load(g)

        log("Old configuration:", old_config)

        with job.options_file.open(encoding='utf8') as f:
            target_configuration = json.load(f)

        log("target_configuration:", target_configuration)
        new_config = dict(old_config, liquid=target_configuration)

        log("New configuration:", new_config)

        with config_yml.open('w', encoding='utf8') as g:
            yaml.dump(new_config, g)

        run_shell(
            'sudo PYTHONUNBUFFERED=1 bin/install --tags configure',
            cwd=str(setup),
        )
        run_shell('sudo supervisorctl restart all')

        state_db.patch(job=None)
        job.options_file.unlink()
        log("Finished")

    log("Released lock")


def daemonize(job_id, var, setup):
    """ daemonize, so we don't get killed by the caller of `launch` """
    with daemon.DaemonContext():
        job = Job(job_id, var)
        with job.open_logfile('a') as f:
            call_self_in_subprocess(
                'run', job_id, var, setup,
                stdout=f, stderr=f,
                env=dict(os.environ, PYTHONUNBUFFERED='1'),
            )


if __name__ == '__main__':
    [stage, job_id, var, setup] = sys.argv[1:]
    if stage == 'daemonize':
        daemonize(job_id, var, setup)

    else:
        do_the_job(job_id, Path(var), Path(setup))
