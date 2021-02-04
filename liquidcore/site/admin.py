from django.conf import settings
from django.contrib.auth.admin import User, UserAdmin
from django.contrib.admin import site

if settings.LIQUID_2FA:
    from django_otp.admin import OTPAdminSite as AdminSite
else:
    from django.contrib.admin import AdminSite

from liquidcore.home.admin import ProfileInline


class HooverAdminSite(AdminSite):
    site_header = "Liquid Core administration"


class HooverUserAdmin(UserAdmin):
    actions = []

    if settings.LIQUID_2FA:
        from ..twofactor.invitations import create_invitations
        actions.append(create_invitations)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
    )

    inlines = (ProfileInline,)

    list_display = ('username', 'email', 'first_name', 'last_name',
                    'organization', 'contact_info', 'about',
                    'is_staff', 'is_superuser', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name',
                     'profile__organization', 'profile__contact_info',
                     'profile__about')

    list_select_related = ('profile', )

    def organization(self, instance):
        return instance.profile.organization

    def contact_info(self, instance):
        return instance.profile.contact_info

    def about(self, instance):
        return instance.profile.about

    organization.short_description = 'Organization'
    contact_info.short_description = 'Contact Info'
    about.short_description = 'About'


liquid_admin = HooverAdminSite(name='liquidadmin')

for model, model_admin in site._registry.items():
    model_admin_cls = type(model_admin)

    if model is User:
        model_admin_cls = HooverUserAdmin

    if model._meta.app_label == 'otp_totp':
        continue

    liquid_admin.register(model, model_admin_cls)
