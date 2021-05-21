import os
import json
from pathlib import Path
from datetime import timedelta


def bool_env(value):
    return (value or '').lower() in ['on', 'true']


def get_interval(spec):
    if not spec:
        return None

    if spec.endswith('d'):
        return timedelta(days=int(spec[:-1]))

    if spec.endswith('h'):
        return timedelta(hours=int(spec[:-1]))

    if spec.endswith('m'):
        return timedelta(minutes=int(spec[:-1]))

    if spec.endswith('s'):
        return timedelta(seconds=int(spec[:-1]))

    raise RuntimeError(f"Can't parse interval {spec!r}")


base_dir = Path(__file__).parent.parent.parent

DEBUG = bool_env(os.environ.get('DEBUG'))
SECRET_KEY = os.environ.get('SECRET_KEY')
liquid_http_protocol = os.environ.get('LIQUID_HTTP_PROTOCOL', 'http')
LIQUID_DOMAIN = os.getenv("LIQUID_DOMAIN")
LIQUID_TITLE = os.getenv('LIQUID_TITLE')
service_address = os.environ.get('SERVICE_ADDRESS')
LIQUID_2FA = bool_env(os.environ.get('LIQUID_2FA'))
LIQUID_URL = f'{liquid_http_protocol}://{LIQUID_DOMAIN}'
LIQUID_APPS = json.loads(os.environ.get('LIQUID_APPS', "null"))
LIQUID_VERSION = os.getenv("LIQUID_VERSION")
LIQUID_CORE_VERSION = os.getenv("LIQUID_CORE_VERSION")

ALLOWED_HOSTS = [LIQUID_DOMAIN]
if service_address:
    ALLOWED_HOSTS.append(service_address)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'oauth2_provider',
    'corsheaders',
    'liquidcore.home',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'liquidcore.home.autologout.AutoLogoutMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTH_STAFF_ONLY = bool_env(os.environ.get('AUTH_STAFF_ONLY'))

AUTH_AUTO_LOGOUT = get_interval(os.environ.get('AUTH_AUTO_LOGOUT', '100d'))
AUTH_AUTO_LOGOUT_SECONDS = int(AUTH_AUTO_LOGOUT.total_seconds())
SESSION_COOKIE_AGE = AUTH_AUTO_LOGOUT_SECONDS
SESSION_COOKIE_NAME = 'liquidcore-sessionid'

if LIQUID_2FA:
    INSTALLED_APPS += [
        'liquidcore.twofactor',
        'django_otp',
        'django_otp.plugins.otp_totp',
    ]

    MIDDLEWARE += [
        'django_otp.middleware.OTPMiddleware',
    ]

    LIQUID_2FA_APP_NAME = LIQUID_DOMAIN

    _valid = os.environ.get('LIQUID_2FA_INVITATION_VALID')
    LIQUID_2FA_INVITATION_VALID = int(_valid or 30)  # minutes


AUTHENTICATION_BACKENDS = [
    'oauth2_provider.backends.OAuth2Backend',
    'liquidcore.home.auth.AuthBackend',
]

ROOT_URLCONF = 'liquidcore.site.urls'
LOGIN_REDIRECT_URL = '/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'liquidcore.site.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(base_dir / 'var' / 'db.sqlite3'),
    }
}


AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = str(base_dir / 'static')

CSRF_COOKIE_NAME = 'liquidcore-csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_LIQUIDCORE_CSRFTOKEN'
X_FRAME_OPTIONS = 'SAMEORIGIN'

OAUTH2_PROVIDER = {
    'ACCESS_TOKEN_EXPIRE_SECONDS': AUTH_AUTO_LOGOUT_SECONDS,
    'REFRESH_TOKEN_EXPIRE_SECONDS': AUTH_AUTO_LOGOUT_SECONDS,
    'AUTHORIZATION_CODE_EXPIRE_SECONDS': 600,  # recommended from docs
    'REFRESH_TOKEN_GRACE_PERIOD_SECONDS': 120,  # recommended from docs
}
