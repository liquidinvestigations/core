from django.contrib.auth.forms import PasswordChangeForm
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import django_otp


class OtpPasswordChangeForm(PasswordChangeForm):

    error_messages = {
        **PasswordChangeForm.error_messages,
        'token_incorrect': _("Invalid Token. Please try again."),
    }

    otp_token = forms.CharField(
        label=_("OTP token"),
        widget=forms.TextInput())

    def clean_otp_token(self):
        otp_token = self.cleaned_data["otp_token"]
        if not django_otp.match_token(self.user, otp_token):
            raise ValidationError(
                self.error_messages['token_incorrect'],
                code='token_incorrect',
                    )
        return otp_token
