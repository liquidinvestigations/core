import subprocess
from django.conf import settings


def status():
    command = "{} status".format(settings.LIQUID_SUPERVISORCTL)
    out = subprocess.check_output(command, shell=True).decode('latin1')

    rv = {}
    for line in out.strip().splitlines():
        [name, status] = line.split()[:2]
        rv[name] = status.lower()

    return rv
