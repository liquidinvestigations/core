import logging
import json
import datetime

import requests

from django.utils import timezone
from .models import HealthCheckPing
from django.conf import settings


log = logging.getLogger(__name__)
HEALTH_CHECK_INFO = settings.HEALTH_CHECK_INFO
CONSUL_URL = settings.HEALTH_CHECK_CONSUL_URL
NOMAD_URL = settings.HEALTH_CHECK_NOMAD_URL
HISTORY_HOURS = 1
CACHE_FILE = '/tmp/latest-health-check-info.json'


def nomad_get(path):
    return requests.get(NOMAD_URL + '/v1/' + path).json()


def consul_get(path):
    return requests.get(CONSUL_URL + '/v1/' + path).json()


def reset():
    """Reset health checks: delete all old values and make new one."""
    HealthCheckPing.objects.all().delete()
    update()


def update():
    """Update health check state.

    Fetch all health checks and save results in db,
    then delete old results.
    Finally, generate and store report in cache file.
    """

    cutoff_date = timezone.now() - datetime.timedelta(hours=HISTORY_HOURS)
    HealthCheckPing.objects.filter(date__lt=cutoff_date).delete()

    HealthCheckPing(result=fetch_health_checks()).save()

    with open(CACHE_FILE, 'w') as f:
        json.dump(_build_report(), f, indent=2)


def _build_report():
    """Fetch all objects from DB and generate report."""
    data = [
        {
            'date': str(x.date.replace(microsecond=0)),
            'result': x.result,
            'age': (
                str(timezone.now().replace(microsecond=0)
                    - x.date.replace(microsecond=0))
            ),
        }
        for x in HealthCheckPing.objects.order_by('-date').all()
    ]
    return {
        'status': 'ok',
        'raw_data': data,
        'history_hours': HISTORY_HOURS,
    }


def fetch_health_checks():
    """Check all health checks from the configuration,
    taking care to avoid non-healthy nodes."""
    print(HEALTH_CHECK_INFO)
    healthy_nodes = [
        n['Name']
        for n in nomad_get('nodes')
        if n['Status'] == 'ready'
        and n['SchedulingEligibility'] == 'eligible'
    ]
    services = sorted(set([x['service'] for x in HEALTH_CHECK_INFO]))
    assert len(services) == len(HEALTH_CHECK_INFO), \
        'found non-unique service names!'
    result = {x['service'] + ':' + x['check']: x for x in HEALTH_CHECK_INFO}
    for val in result.values():
        val['ok'] = False
        val['status'] = 'missing'
    for service in services:
        for check in consul_get(f'/health/checks/{service}'):
            key = service + ':' + check['Name']
            if check['Node'] not in healthy_nodes:
                continue
            result[key]['status'] = check['Status']
            result[key]['ok'] = (check['Status'] == 'passing')
    return result


def print_report():
    """Print json object with the current state of the health checks."""
    # data = get_report()
    print(HEALTH_CHECK_INFO)
    data = fetch_health_checks()
    print(json.dumps(data, indent=2))


def get_report():
    """Fetch the health check report from cache."""

    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        log.exception(e)
        log.error('health check cache not found: %s', CACHE_FILE)
        return None
