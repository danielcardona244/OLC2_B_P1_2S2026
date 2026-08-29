import os

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'web.settings',
)

import django
django.setup()

from django.test import Client


def test_home_responde_200():
    response = Client().get('/')

    assert response.status_code == 200


def test_home_usa_template_principal():
    response = Client().get('/')

    assert 'OxigenScript' in response.content.decode('utf-8')


def test_gui_tiene_acciones_archivo_obligatorias():
    html = Client().get('/').content.decode('utf-8')

    assert 'id="new-file-btn"' in html
    assert 'id="open-file-btn"' in html
    assert 'id="save-file-btn"' in html


def test_gui_tiene_boton_ejecutar_y_reportes():
    html = Client().get('/').content.decode('utf-8')

    assert 'id="run-btn"' in html
    assert 'id="reports-btn"' in html


def test_gui_tiene_editor_y_numeracion_lineas():
    html = Client().get('/').content.decode('utf-8')

    assert 'id="code-editor"' in html
    assert 'id="line-numbers"' in html


def test_gui_tiene_consola():
    html = Client().get('/').content.decode('utf-8')

    assert 'id="console-output"' in html
    assert 'id="execution-time"' in html


def test_gui_tiene_tabs_reportes():
    html = Client().get('/').content.decode('utf-8')

    assert 'data-tab="errors"' in html
    assert 'data-tab="symbols"' in html
    assert 'data-tab="ast"' in html


def test_gui_carga_css_y_javascript():
    html = Client().get('/').content.decode('utf-8')

    assert '/static/css/app.css' in html
    assert '/static/js/app.js' in html


def test_gui_muestra_puerto_oficial_7810():
    html = Client().get('/').content.decode('utf-8')

    assert '127.0.0.1:7810' in html


def test_gui_tiene_boton_abrir_ast():
    html = Client().get('/').content.decode('utf-8')

    assert 'id="open-ast-btn"' in html
    assert 'Abrir AST en pestaña' in html