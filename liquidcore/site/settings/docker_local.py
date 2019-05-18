import re

from .common import *

DEBUG = True
SECRET_KEY = 'foo'
ALLOWED_HOSTS = ['*']
AUTH_PASSWORD_VALIDATORS = []
INVOKE_HOOK = 'echo'

HOOVER_APP_URL = os.environ.get('HOOVER_APP_URL')
DOKUWIKI_APP_URL = os.environ.get('DOKUWIKI_APP_URL')
RIOT_APP_URL = os.environ.get('RIOT_APP_URL')
NEXTCLOUD_APP_URL = os.environ.get('NEXTCLOUD_APP_URL')
