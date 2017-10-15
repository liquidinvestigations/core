from pathlib import Path
import pytest
from django.test.utils import override_settings
from django.conf import settings
from liquidcore.config import reconfigure, agent


@pytest.fixture(autouse=True)
def mock_target_configuration(monkeypatch):
    value = {}

    def set_value(new_value):
        value = new_value

    monkeypatch.setattr(reconfigure, 'get_configuration', lambda: value)

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
    mock_setup_dir = Path(tmpdir.mkdir('setup'))
    core_var_dir = Path(tmpdir.mkdir('var'))

    libexec = mock_setup_dir / 'libexec'
    libexec.mkdir(mode=0o755)
    setup_configure = libexec / 'liquid-core-configure'

    class setup:
        def write_configure_script(configure_src):
            with setup_configure.open('w', encoding='utf8') as f:
                f.write(configure_src)
            setup_configure.chmod(0o755)

    setup.write_configure_script(MOCK_LIQUID_CORE_CONFIG)

    with override_settings():
        settings.LIQUID_CORE_VAR = str(core_var_dir)
        settings.LIQUID_SETUP_DIR = str(mock_setup_dir)

        yield setup


def test_run_one_job():
    job = reconfigure.reconfigure_system()
    job.wait()


def test_detect_failed_job(setup):
    setup.write_configure_script(MOCK_FAIL_LIQUID_CORE_CONFIG)
    job = reconfigure.reconfigure_system()

    with pytest.raises(agent.JobFailed):
        job.wait()
