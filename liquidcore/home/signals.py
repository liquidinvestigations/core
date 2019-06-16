from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_out


@receiver(user_logged_out)
def delete_oauth2_tokens(user, **kwargs):
    user.oauth2_provider_accesstoken.all().delete()
    user.oauth2_provider_refreshtoken.all().delete()
