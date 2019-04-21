DEBUG = os.environ.get('DEBUG', '').lower() in ['yes', 'true', '1', 'on']

SECRET_KEY = os.environ.get('SECRET_KEY')

host = os.environ.get('HTTP_HOST')
ALLOWED_HOSTS = [host] if host else []

AUTH_PASSWORD_VALIDATORS = []
INVOKE_HOOK = 'echo'
