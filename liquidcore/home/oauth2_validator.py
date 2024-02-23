from django.conf import settings
from oauth2_provider.oauth2_validators import OAuth2Validator


class CustomOAuth2Validator(OAuth2Validator):

    def get_additional_claims(self, request):
        fake_user_email = request.user.get_username() + '@' + settings.LIQUID_DOMAIN
        return {
            "sub": fake_user_email,
            "email": fake_user_email,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "name": request.user.username,
        }
