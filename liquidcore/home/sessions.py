import redis
from django.conf import settings

APP_REDIS_IDS = {
    'hoover': 1,
    'dokuwiki': 2,
    'codimd': 3,
    'nextcloud': 4,
}


def clear_authproxy_session(username):
    '''Delete app sessions for all apps stored in redis for that user. '''

    for app_id in APP_REDIS_IDS.values():
        if settings.AUTHPROXY_REDIS_URL:
            r = redis.from_url('redis://'
                               + settings.AUTHPROXY_REDIS_URL + app_id)
            for key in r.scan_iter():
                if r.get(key).startswith(username.encode()):
                    r.delete(key)
