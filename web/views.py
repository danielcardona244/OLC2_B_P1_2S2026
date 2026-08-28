from django.shortcuts import render


def index(request):
    """Pantalla principal del IDE web de OxigenScript."""
    return render(
        request,
        'index.html',
        {
            'app_name': 'OxigenScript',
            'course_code': '0781',
        },
    )
