from django.conf import settings
from django.contrib.auth.admin import User, UserAdmin
from django.contrib.admin import site

if settings.LIQUID_2FA:
    from django_otp.admin import OTPAdminSite as AdminSite
else:
    from django.contrib.admin import AdminSite


class HooverAdminSite(AdminSite):
    site_header = "Liquid Core administration"


class HooverUserAdmin(UserAdmin):
    actions = []

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_staff', 'last_login')

    if settings.LIQUID_2FA:
        from ..twofactor.invitations import create_invitations
        actions.append(create_invitations)


liquid_admin = HooverAdminSite(name='liquidadmin')

for model, model_admin in site._registry.items():
    model_admin_cls = type(model_admin)

    if model is User:
        model_admin_cls = HooverUserAdmin

    if model._meta.app_label == 'otp_totp':
        continue

    liquid_admin.register(model, model_admin_cls)
