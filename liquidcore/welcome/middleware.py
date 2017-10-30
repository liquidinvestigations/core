from django.http import HttpResponseRedirect
from .views import should_welcome


def welcome_middleware(get_response):

    def middleware(request):
        if should_welcome():
            if not request.path.startswith('/welcome/'):
                return HttpResponseRedirect('/welcome/')

        return get_response(request)

    return middleware
