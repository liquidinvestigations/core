import uuid

from django.db import models
from django.contrib.auth import get_user_model


def random_uuid():
    return str(uuid.uuid4())


class Profile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    organization = models.TextField(max_length=500, blank=True)
    contact_info = models.TextField(max_length=100, blank=True)
    about = models.TextField(max_length=4000, null=True, blank=True)
    uuid = models.CharField(max_length=100, null=False, blank=False,
                            default=random_uuid)
