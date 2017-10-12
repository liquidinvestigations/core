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


def _do_the_job(job_id, var, setup):
    """
    Perform useful work, since by now we're in our own little world, with
    stdout+stderr redirected to the log file.
    """
    job = _Job(job_id, var)
    _log("Acquiring agent lock")
    with _lock(var / 'agent.lock'):
        _log("Acquired lock")

        with job._task_file.open(encoding='utf8') as f:
            target_configuration = json.load(f)

        _log("target_configuration:", target_configuration)

        # TODO apply the configuration using ansible

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
