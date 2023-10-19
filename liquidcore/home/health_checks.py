from collections import defaultdict
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
HISTORY_HOURS = 2
COLOR_BAR_COUNT = 50
CACHE_FILE = '/tmp/latest-health-check-info.json'


def get_json_default(url, default_val):
    try:
        return requests.get(url).json() or default_val
    except Exception as e:
        log.debug(str(e))
        return default_val


def nomad_get(path):
    return get_json_default(NOMAD_URL + '/v1/' + path, dict())


def consul_get(path):
    return get_json_default(CONSUL_URL + '/v1/' + path, dict())


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

    try:
        new_checks = fetch_health_checks()
    except Exception as e:
        log.warning('error fetching health checks: %s', str(e))
        log.exception(e)
        return

    cutoff_date = timezone.now() - datetime.timedelta(hours=HISTORY_HOURS)
    HealthCheckPing.objects.filter(date__lt=cutoff_date).delete()

    HealthCheckPing(result=new_checks).save()

    with open(CACHE_FILE, 'w') as f:
        json.dump(_build_report(), f, indent=2)


def _build_report():
    """Fetch all objects from DB and generate report."""
    data = [
        {
            'result': x.result,
            'date': str(x.date.replace(microsecond=0)),
            'age': (
                str(timezone.now().replace(microsecond=0)
                    - x.date.replace(microsecond=0))
            ),
        }
        for x in HealthCheckPing.objects.order_by('-date').all()
    ]
    historical_fail_counter = defaultdict(int)
    for x in data:
        for failing in x['result']['failing_checks']:
            frozen = tuple(failing.items())
            historical_fail_counter[frozen] += 1
    historical_fails = []
    for frozen, fail_count in historical_fail_counter.items():
        item = dict(frozen)
        item['fail_count'] = fail_count
        item['total_count'] = len(data)
        historical_fails.append(item)
    historical_fails = sorted(historical_fails, key=lambda x: -x['fail_count'])

    app_color_bars = defaultdict(list)
    for data_point in data:
        for app, healthy in data_point['result']['app_health'].items():
            app_color_bars[app].append('green' if healthy else 'red')

    for app in app_color_bars:
        while len(app_color_bars[app]) < COLOR_BAR_COUNT:
            app_color_bars[app].append('gray')
        # ensure item count & correct order
        app_color_bars[app] = app_color_bars[app][:COLOR_BAR_COUNT]
        app_color_bars[app] = app_color_bars[app][::-1]

    def compute_uptime_str(color_bars):
        count_total = 0
        count_success = 0
        for bar in color_bars:
            if bar == 'green':
                count_total += 1
                count_success += 1
            if bar == 'red':
                count_total += 1
        if count_total == 0:
            count_total += 1
        return f'Uptime in last {HISTORY_HOURS}h: ' \
            + str(int(100.0 * count_success / count_total)) + '%'

    app_color_bars = {
        app: {
            'colors': app_color_bars[app],
            'uptime_percent': compute_uptime_str(app_color_bars[app]),
        }
        for app in app_color_bars
    }

    report = {
        'raw_results': data,
        'all_currently_ok': data[0]['result']['ok'],
        'all_history_ok': all(x['result']['ok'] for x in data),
        'app_color_bars': app_color_bars,
        'historical_fails': historical_fails,
        'history_hours': HISTORY_HOURS,
    }
    if report['all_currently_ok'] and report['all_history_ok']:
        report['status_message'] = 'OK'
        report['status_color'] = 'green'
    elif report['all_currently_ok'] and not report['all_history_ok']:
        report['status_message'] = 'Intermittent Failures'
        report['status_color'] = 'orange'
    else:
        report['status_message'] = 'Error -- Some Apps Offline'
        report['status_color'] = 'red'
    return report


def fetch_health_checks():
    """Check all health checks from the configuration,
    taking care to avoid non-healthy nodes."""

    def pick_worst(a, b):
        if not a and not b:
            return 'missing'
        for s in ['critical', 'warning', 'passing']:
            if s in [a, b]:
                return s
        raise RuntimeError(f'Unknown status: "{a}" and "{b}"')

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

            result[key] = result.get(key, {})
            result[key]['status'] = pick_worst(
                check['Status'],
                result[key].get('status'),
            )
            result[key]['ok'] = (check['Status'] == 'passing')

    failing_checks = [x for x in result.values() if not x['ok']]
    app_health = {
        app: all(x['ok'] for x in result.values() if x['app'] == app)
        for app in sorted(set(x['app'] for x in result.values()))
    }
    return {
        'failing_checks': failing_checks,
        'fail_count': len(failing_checks),
        'total_count': len(result.keys()),
        'pass_count': len(result.keys()) - len(failing_checks),
        'app_health': app_health,
        'ok': bool(not failing_checks),
    }


def print_report():
    """Print json object with the current state of the health checks."""
    data = get_report()
    # data = fetch_health_checks()
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
