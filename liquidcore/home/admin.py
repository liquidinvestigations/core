from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

from liquidcore.home.models import Profile

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

    # def get_inline_instances(self, request, obj=None):
    #     if not obj:
    #         return list()
    #     return super(UserAdmin, self).get_inline_instances(request, obj)
    def get_inline_instances(self, request, obj=None):
        return [inline(self.model, self.admin_site) for inline in self.inlines]

    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_staff', 'organization', 'contact_info', 'about')
    list_select_related = ('profile', )

    def organization(self, instance):
        return instance.profile.location

    def contact_info(self, instance):
        return instance.profile.contact_info

    def about(self, instance):
        return instance.profile.about

    organization.short_description = 'Organization'
    contact_info.short_description = 'Contact Info'
    about.short_description = 'About'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
