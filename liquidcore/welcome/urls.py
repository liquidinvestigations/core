from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^done/$', views.welcome_done),
    url(r'^$', views.welcome),
]
