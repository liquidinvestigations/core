import redis
from django.conf import settings


def clear_authproxy_session(username):
    '''Delete app sessions for all apps stored in redis for that user. '''
    APP_REDIS_IDS = {
        v['id']: v.get('redis_id')
        for v in settings.LIQUID_APPS
        if v.get('redis_id')
    }
    for app_id in APP_REDIS_IDS.values():
        if settings.AUTHPROXY_REDIS_URL:
            r = redis.from_url(settings.AUTHPROXY_REDIS_URL + str(app_id))
            for key in r.scan_iter():
                if r.get(key).startswith(username.encode()):
                    r.delete(key)
