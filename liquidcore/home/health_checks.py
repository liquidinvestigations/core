import logging
import json
from datetime import datetime

from django.utils import timezone
from django.db.models import HealthCheckPing
from django.conf import settings


log = logging.getLogger(__name__)
HEALTH_CHECK_INFO = settings.HEALTH_CHECK_INFO
CONSUL_URL = settings.HEALTH_CHECK_CONSUL_URL


def reset():
    """Reset health checks: delete all old values."""
    HealthCheckPing.objects.delete()


def update():
    """Fetch all health checks and save results
    in db, then delete old results."""

    one_hour_ago = timezone.now() - datetime.timedelta(hours=1)
    HealthCheckPing.objects.filter(date_lt=one_hour_ago).delete()

    HealthCheckPing(result=fetch_health_checks()).save()


def fetch_health_checks():
    return {'todo': 'all'}


def print_summary():
    print(json.dumps(get_summary, indent=2))


def get_summary():
    data = [{'date': x.date, 'result': x.result}
            for x in HealthCheckPing.objects.all()]
    return {'status': 'ok', 'count': len(data), 'data': data}
