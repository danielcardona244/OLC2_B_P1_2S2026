from django.urls import include, path


urlpatterns = [
    path(
        'api/',
        include('web.api.urls'),
    ),
]
