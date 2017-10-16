from pathlib import Path
import pytest
from django.test.utils import override_settings
from django.conf import settings
from liquidcore.config import system, agent


@pytest.fixture(autouse=True)
def mock_target_configuration(monkeypatch):
    value = {}

    def set_value(new_value):
        nonlocal value
        value = new_value

    monkeypatch.setattr(system, 'get_configuration', lambda: value)

    return set_value


MOCK_LIQUID_CORE_CONFIG = """\
#!/usr/bin/env python3
print("hello from mock setup")
"""


MOCK_FAIL_LIQUID_CORE_CONFIG = """\
#!/usr/bin/env python3
raise RuntimeError("please just die.")
"""


@pytest.fixture(autouse=True)
def setup(tmpdir, monkeypatch):
    mock_setup_dir = Path(str(tmpdir.mkdir('setup')))
    core_var_dir = Path(str(tmpdir.mkdir('var')))

    libexec = mock_setup_dir / 'libexec'
    libexec.mkdir(mode=0o755)
    setup_configure = libexec / 'liquid-core-configure'

    class setup:
        def mock(content=None, succeeds=True):
            by_outcome = {
                True: MOCK_LIQUID_CORE_CONFIG,
                False: MOCK_FAIL_LIQUID_CORE_CONFIG,
            }
            with setup_configure.open('w', encoding='utf8') as f:
                f.write(content or by_outcome[succeeds])
            setup_configure.chmod(0o755)

    setup.mock()

    setup.core_var_dir = core_var_dir

    with override_settings():
        settings.LIQUID_CORE_VAR = str(core_var_dir)
        settings.LIQUID_SETUP_DIR = str(mock_setup_dir)

        yield setup


def test_run_one_job():
    job = system.reconfigure_system()
    job.wait()


def test_detect_failed_job(setup):
    setup.mock(succeeds=False)
    job = system.reconfigure_system()

    with pytest.raises(agent.JobFailed):
        job.wait()


def test_failed_job_marks_system_as_broken(setup):
    setup.mock(succeeds=False)

    def reconfigure(**kwargs):
        return system.reconfigure_system(**kwargs).wait()

    with pytest.raises(agent.JobFailed):
        reconfigure()

    # system is in "broken" state; jobs will fail until we run "repair"

    setup.mock(succeeds=True)

    with pytest.raises(agent.JobFailed):
        reconfigure()

    with pytest.raises(agent.JobFailed):
        reconfigure()

    reconfigure(repair=True)
    # system is repaired; next jobs will run happily.

    reconfigure()
    reconfigure()


TEST_CONCURRENCY_WHOAMI = """\
#!/usr/bin/env python3
import time
import sys
import json

options = json.load(sys.stdin)

def stamp_time(n):
    filename = '{}{}.txt'.format(options['vars']['prefix'], n)
    with open(filename, 'w', encoding='utf8') as f:
        print(time.time(), file=f)

stamp_time(0)
time.sleep(3)
stamp_time(1)
"""


def test_concurrency(setup, mock_target_configuration):
    setup.mock(TEST_CONCURRENCY_WHOAMI)

    mock_target_configuration({'prefix': '{}/a'.format(setup.core_var_dir)})
    job1 = system.reconfigure_system()
    mock_target_configuration({'prefix': '{}/b'.format(setup.core_var_dir)})
    job2 = system.reconfigure_system()

    job1.wait()
    job2.wait()

    with job1.open_logfile() as f: print(f.read())
    with job2.open_logfile() as f: print(f.read())

    def t(name):
        path = setup.core_var_dir / (name + '.txt')
        with path.open(encoding='utf8') as f:
            return float(f.read())

    (a0, a1, b0, b1) = t('a0'), t('a1'), t('b0'), t('b1')
    assert (a0 < a1 < b0 < b1) or (b0 < b1 < a0 < a1)
