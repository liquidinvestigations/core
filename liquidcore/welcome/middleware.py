from django.http import HttpResponseRedirect


def welcome_middleware(get_response):

    def middleware(request):
        if not request.path.startswith('/welcome/'):
            return HttpResponseRedirect('/welcome/')

        return get_response(request)

    return middleware
