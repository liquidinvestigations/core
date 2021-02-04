from django.contrib import admin
from django.contrib.auth import get_user_model

from liquidcore.home.models import Profile

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'
    fields = ('user', 'organization', 'contact_info', 'about')
    readonly_fields = ('user',)
    list_display = ('user', 'organization', 'contact_info', 'about')
    search_fields = ('organization', 'contact_info', 'about',)
