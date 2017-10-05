from rest_framework.permissions import IsAdminUser

# source: https://github.com/sebastibe/django-rest-skeleton/tree/master/api/users
class IsAdminOrSelf(IsAdminUser):
    """
    Allow access to admin users or the user himself.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        elif (request.user and type(obj) == type(request.user) and
              obj == request.user):
            return True
        return False
