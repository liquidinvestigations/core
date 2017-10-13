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

import sys
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

    job = _Job(_timestamp(), var)
    with job._task_file.open('w', encoding='utf8') as f:
        print(json.dumps(task_data, indent=2), file=f)

    _call_self_in_subprocess('daemonize', job.id, var, setup)

    return job


def _timestamp():
    return str(datetime.utcnow().isoformat())


class _Job:

    """
    A configuration job. This class does not encapsulate any configuration
    logic, only the job's metadata.
    """

    def __init__(self, id, var):
        self.id = id
        self.var = Path(var)

    @property
    def _task_file(self):
        return self.var / 'task-{}.json'.format(self.id)

    def is_finished(self):
        return not self._task_file.exists()

    def open_logfile(self, mode='r'):
        logs = self.var / 'logs'
        logs.mkdir(mode=0o755, exist_ok=True)
        logfile = logs / 'agent-{}.log'.format(self.id)
        if mode == 'r' and not logfile.exists():
            logfile.touch()
        return logfile.open(mode, encoding='utf8')


@contextmanager
def _lock(path):
    with open(str(path), 'w') as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def _call_self_in_subprocess(*args, **kwargs):
    argv = [sys.executable, __file__] + [str(a) for a in args]
    subprocess.run(argv, check=True, **kwargs)


def _log(*args):
    print(*args, _timestamp())


class _State:

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


def _do_the_job(job_id, var, setup):
    """
    Perform useful work, since by now we're in our own little world, with
    stdout+stderr redirected to the log file.
    """
    job = _Job(job_id, var)
    state_db = _State(var)
    _log("Acquiring agent lock")
    with _lock(var / 'agent.lock'):
        _log("Acquired lock")
        if state_db.load().get('job'):
            raise RuntimeError("Another job was running and did not finish")
        state_db.patch(job=job_id)

        config_yml = setup / 'ansible' / 'vars' / 'config.yml'
        with config_yml.open(encoding='utf8') as g:
            old_config = yaml.load(g)

        _log("Old configuration:", old_config)

        with job._task_file.open(encoding='utf8') as f:
            target_configuration = json.load(f)

        _log("target_configuration:", target_configuration)
        new_config = dict(old_config, liquid=target_configuration)

        _log("New configuration:", new_config)

        with config_yml.open('w', encoding='utf8') as g:
            yaml.dump(new_config, g)

        # TODO run('bin/install --tags configure', cwd=str(setup))
        # TODO supervisorctl restart all

        state_db.patch(job=None)
        job._task_file.unlink()
        _log("Finished")

    _log("Released lock")


def _daemonize(job_id, var, setup):
    """ daemonize, so we don't get killed by the caller of `launch` """
    with daemon.DaemonContext():
        job = _Job(job_id, var)
        with job.open_logfile('a') as f:
            _call_self_in_subprocess(
                'run', job_id, var, setup,
                stdout=f, stderr=f,
            )


if __name__ == '__main__':
    [stage, job_id, var, setup] = sys.argv[1:]
    if stage == 'daemonize':
        _daemonize(job_id, var, setup)

    else:
        _do_the_job(job_id, Path(var), Path(setup))
