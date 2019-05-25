from django.conf import settings
from django.contrib.auth.admin import User, UserAdmin

if settings.LIQUID_2FA:
    from django_otp.admin import OTPAdminSite as AdminSite
else:
    from django.contrib.admin import AdminSite


class HooverAdminSite(AdminSite):
    pass


class HooverUserAdmin(UserAdmin):
    actions = []

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    if settings.LIQUID_2FA:
        from ..twofactor.invitations import create_invitations
        actions.append(create_invitations)


admin_site = HooverAdminSite(name='hoover-admin')
admin_site.register(User, HooverUserAdmin)
