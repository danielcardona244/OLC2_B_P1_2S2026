from django.urls import path
from web.api import views

app_name = 'oxigenscript_api'
urlpatterns = [
    path('health/', views.health, name='health'),
    path('execute/', views.execute_code, name='execute'),
    path('reports/errors/', views.errors_report, name='errors_report'),
    path('reports/symbols/', views.symbols_report, name='symbols_report'),
    path('reports/ast/', views.ast_report, name='ast_report'),
]
