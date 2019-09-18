import string
from django.contrib.auth.models import AbstractUser

USERNAME_CHARS = string.ascii_letters + string.digits + '.'


class User(AbstractUser):
    class Meta:
        db_table = 'auth_user'

    def save(self, *args, **kwargs):
        assert all(x in USERNAME_CHARS for x in self.username), 'Bad Username'
        super(User, self).save(*args, **kwargs)
