from django.urls import include, path

from web import views


urlpatterns = [
    path(
        '',
        views.index,
        name='index',
    ),
    path(
        'api/',
        include('web.api.urls'),
    ),
]
