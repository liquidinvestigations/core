from django import forms
from django.conf import settings
from django.contrib.auth.admin import User, Group, UserAdmin, GroupAdmin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import CheckboxSelectMultiple, ModelForm
from django.contrib.admin import site, ModelAdmin
from django.utils.timezone import now

if settings.LIQUID_2FA:
    from django_otp.admin import OTPAdminSite as AdminSite
    from ..twofactor.models import Invitation
else:
    from django.contrib.admin import AdminSite


class HooverAdminSite(AdminSite):
    site_header = "Liquid Core administration"


class PermissionFilterMixin(object):
    '''Filter permissions field in the admin panel to show only app
    permisssions.

    Changes the manytomany formfield for the django permissions, by filtering
    all permissions but the ones to allow app usage.
    '''
    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name in ('permissions', 'user_permissions'):
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            qs = _filter_permissions(qs)
            kwargs['queryset'] = qs

        return super(PermissionFilterMixin, self).formfield_for_manytomany(
            db_field, request, **kwargs)


def _filter_permissions(qs):
    '''Filter the permission queryset to show only enabled apps.

    Gets a queryset as input and filters it based on the LIQUID_APPS setting.
    '''
    return qs.filter(codename__in=(
        [f'use_{perm}' for perm in
         [app['id']for app in settings.LIQUID_APPS if app['enabled']]]
    ))


def all_permissions():
    '''Helper function that returns a set of all app permissions as strings.'''
    return {f'home.use_{perm}' for perm in
            [app['id'] for app in settings.LIQUID_APPS
             if app['enabled'] and not app['adminOnly']]}


class HooverUserAdmin(PermissionFilterMixin, UserAdmin):
    actions = []

    def get_form(self, request, obj=None, **kwargs):
        form = super(HooverUserAdmin, self).get_form(request, obj, **kwargs)
        if 'user_permissions' in form.base_fields:
            form.base_fields['user_permissions'].widget = (
                CheckboxSelectMultiple())
        return form

    def user_app_permissions(self, obj):
        return [perm.codename for perm in obj.user_permissions.all()]

    def app_permissions_from_groups(self, obj):
        perm_set = obj.get_group_permissions()
        if all_permissions().issubset(perm_set):
            return 'All app permissions.'
        if perm_set:
            return [perm.split('.')[1] for perm in perm_set
                    if perm in all_permissions()]
        else:
            return '-'

    def user_groups(self, obj):
        groups = obj.groups.all()
        if not groups:
            return ''
        return [group for group in groups]

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active',
                       'is_staff',
                       'is_superuser',
                       'groups',
                       'app_permissions_from_groups',
                       'user_permissions',
                       ),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_staff', 'is_superuser',
                    'last_login', 'user_app_permissions',
                    'user_groups', 'app_permissions_from_groups')

    readonly_fields = ('app_permissions_from_groups',)

    if settings.LIQUID_2FA:
        from ..twofactor.invitations import create_invitations
        actions.append(create_invitations)


class GroupAdminForm(ModelForm):
    class Meta:
        model = Group
        exclude = []

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('users', False)
    )

    def __init__(self, *args, **kwargs):
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['users'].initial = self.instance.user_set.all()

    def save_m2m(self):
        self.instance.user_set.set(self.cleaned_data['users'])

    def save(self, *args, **kwargs):
        instance = super(GroupAdminForm, self).save()
        self.save_m2m()
        return instance


class HooverGroupAdmin(PermissionFilterMixin, GroupAdmin):

    def get_form(self, request, obj=None, **kwargs):
        kwargs['form'] = GroupAdminForm
        form = super(HooverGroupAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['permissions'].widget = CheckboxSelectMultiple()
        return form

    def group_app_permissions(self, obj):
        return [perm.codename for perm in obj.permissions.all()]

    fields = ['name', 'users', 'permissions']
    list_display = ('name', 'group_app_permissions',)


class InvitationAdmin(ModelAdmin):
    list_display = ('user', 'get_url', 'expires', 'time_left', 'state')

    def get_url(self, invitation):
        return f'{settings.LIQUID_URL}/invitation/{invitation.code}'

    def time_left(self, invitation):
        if (invitation.expires) < now():
            return ''
        else:
            minutes_left = int((invitation.expires - now())
                               .total_seconds() / 60)
            return f'{minutes_left} min'

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


liquid_admin = HooverAdminSite(name='liquidadmin')

for model, model_admin in site._registry.items():
    model_admin_cls = type(model_admin)

    if model is User:
        model_admin_cls = HooverUserAdmin

    if model is Group:
        model_admin_cls = HooverGroupAdmin

    if model._meta.app_label == 'otp_totp':
        continue

    if model._meta.app_label == 'oauth2_provider':
        continue

    liquid_admin.register(model, model_admin_cls)

if settings.LIQUID_2FA:
    liquid_admin.register(Invitation, InvitationAdmin)
