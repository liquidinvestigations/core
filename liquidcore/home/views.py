from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

def homepage(request):
    return render(request, 'homepage.html')

def profile(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponse('Unauthorized', status=401)
    return JsonResponse({
        'login': user.get_username(),
        'email': user.email,
    })
