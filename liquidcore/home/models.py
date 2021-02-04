
from django.db import models
from django.contrib.auth import get_user_model


class Profile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    organization = models.TextField(max_length=500, blank=True)
    contact_info = models.TextField(max_length=100, blank=True)
    about = models.TextField(max_length=4000, null=True, blank=True)

    def __str__(self):
        return "Profile for " + self.user.username

    __repr__ = __str__
