"""
Configuration agent for liquid-core

This module does daemonization voodoo. It has two public methods: `launch` and
`status`.

## `agent.launch(options, repair)`
`options` is the configuration that will be applied.

`repair` - if the last job failed, should we attempt to recover? This means
clearing the "failed" flag and re-applying the target configuration. This flag
should only be set when the user explicitly requests a repair, otherwise we'll
be masking errors.

Returns a job object with the following members:

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

## `agent.status()`
Returns a status report of known jobs.

"""

import time
import sys
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import fcntl
import subprocess
import json
import daemon
import psutil


def launch(options, repair):
    """ Launch a job to apply `options`. """
    from django.conf import settings

    var = Path(settings.LIQUID_CORE_VAR)

    task_data = {
        'options': options,
        'command': settings.LIQUID_SETUP_RECONFIGURE,
        'repair': repair,
    }

    job = Job(timestamp(), var)
    with job.options_file.open('w', encoding='utf8') as f:
        print(json.dumps(task_data, indent=2), file=f)

    call_self_in_subprocess('daemonize', job.id, var)

    return job


def status():
    from django.conf import settings
    return enumerate_jobs(Path(settings.LIQUID_CORE_VAR))


def enumerate_jobs(var):
    jobs = defaultdict(dict)

    for item in var.iterdir():
        options_match = re.match(r'^job-(?P<id>.*)\.json$', item.name)
        if options_match:
            job_id = options_match.group('id')
            jobs[job_id]['options'] = True

        pidfile_match = re.match(r'^job-(?P<id>.*)\.pid$', item.name)
        if pidfile_match:
            job_id = pidfile_match.group('id')
            try:
                with item.open(encoding='utf8') as f:
                    jobs[job_id]['pid'] = int(f.read())
            except FileNotFoundError:
                continue

    logs = var / 'logs'
    for item in logs.iterdir():
        logfile_match = re.match(r'^job-(?P<id>.*)\.log$', item.name)
        if logfile_match:
            job_id = logfile_match.group('id')
            with item.open(encoding='utf8') as f:
                jobs[job_id]['log'] = f.read()

    for job_id in jobs:
        jobs[job_id]['job'] = Job(job_id, var)

    return dict(jobs)


def delete_old_jobs(var, keep):
    for job_item in enumerate_jobs(var).values():
        job = job_item['job']
        if job.id == keep:
            continue
        for path in [job.options_file, job.pid_file]:
            if path.is_file():
                path.unlink()


def timestamp():
    return str(datetime.utcnow().isoformat())


class JobFailed(Exception):
    pass


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

    @property
    def pid_file(self):
        return self.var / 'job-{}.pid'.format(self.id)

    def wait(self, launch_timeout=20, dump_logs=True):
        def dump_the_logs():
            if dump_logs:
                with self.open_logfile() as f:
                    print("========", file=sys.stderr)
                    print(f.read(), file=sys.stderr)
                    print("========", file=sys.stderr)

        t0 = time.time()
        while True:
            if not self.options_file.exists():
                # the job finished and deleted its options file
                return

            try:
                with self.pid_file.open(encoding='utf8') as f:
                    pid = int(f.read())
            except FileNotFoundError:
                if time.time() > t0 + launch_timeout:
                    dump_the_logs()
                    raise JobFailed('Job {} failed to launch' .format(self.id))

                continue

            if psutil.pid_exists(pid):
                # the job is running, let's wait a bit
                time.sleep(.2)
                continue

            # look again to make sure the pidfile was not deleted
            if self.pid_file.exists():
                # yep, process is dead but pidfile is in place, it died :(
                dump_the_logs()
                raise JobFailed(
                    'Job {} died, I found its stale pidfile'
                    .format(self.id)
                )

    def open_logfile(self, mode='r'):
        logs = self.var / 'logs'
        logs.mkdir(mode=0o755, exist_ok=True)
        logfile = logs / 'job-{}.log'.format(self.id)
        if mode == 'r' and not logfile.exists():
            logfile.touch()
        return logfile.open(mode, encoding='utf8')


@contextmanager
def lock(path):
    with open(str(path), 'w') as lock_file:
        log("Acquiring lock", path)
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        log("Acquired lock", path)

        try:
            yield

        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            log("Released lock", path)


def call_self_in_subprocess(*args, **kwargs):
    argv = [sys.executable, __file__] + [str(a) for a in args]
    subprocess.run(argv, check=True, **kwargs)


def log(*args):
    print(timestamp(), *args)


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


def run_task(command, options):
    log(
        "Calling setup with target configuration",
        json.dumps(options, indent=2, sort_keys=True)
    )

    subprocess.run(
        command,
        shell=True,
        input=json.dumps(options, indent=2).encode('utf8'),
        check=True,
    )


@contextmanager
def pidfile(pid_file):
    tmp_pid_file = pid_file.parent / (pid_file.name + '.tmp')

    with tmp_pid_file.open('w', encoding='utf8') as f:
        print(os.getpid(), file=f)

    tmp_pid_file.rename(pid_file)

    yield

    # Removing the pidfile means "job completed successfully", so we
    # only remove it if no exception was raised.
    pid_file.unlink()


def do_the_job(job_id, var):
    """
    Perform useful work, since by now we're in our own little world, with
    stdout+stderr redirected to the log file.
    """
    job = Job(job_id, var)
    with pidfile(job.pid_file):
        with job.options_file.open(encoding='utf8') as f:
            task_data = json.load(f)

        repair = task_data.pop('repair')

        state_db = State(var)
        with lock(var / 'agent.lock'):

            if state_db.load().get('job'):
                if not repair:
                    raise RuntimeError(
                        "Another job was running and did not finish")

            state_db.patch(job=job_id)

            run_task(**task_data)

            state_db.patch(job=None)

            if repair:
                delete_old_jobs(var, keep=job_id)

            job.options_file.unlink()

            log("Finished")


def daemonize(job_id, var):
    """ daemonize, so we don't get killed by the caller of `launch` """
    with daemon.DaemonContext():
        job = Job(job_id, var)
        with job.open_logfile('a') as f:
            call_self_in_subprocess(
                'run', job_id, var,
                stdout=f, stderr=f,
                env=dict(os.environ, PYTHONUNBUFFERED='1'),
            )


if __name__ == '__main__':
    [stage, job_id, var] = sys.argv[1:]
    if stage == 'daemonize':
        daemonize(job_id, var)

    else:
        do_the_job(job_id, Path(var))
