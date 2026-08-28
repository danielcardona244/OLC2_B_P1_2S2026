import json
import tempfile
from pathlib import Path

import django
import pytest
from django.test import Client, override_settings

django.setup()

@pytest.fixture
def client():
    return Client()

def post_json(client, payload):
    return client.post('/api/execute/', data=json.dumps(payload), content_type='application/json')

def test_health(client):
    response = client.get('/api/health/')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_execute_rechaza_get(client):
    assert client.get('/api/execute/').status_code == 405

def test_execute_rechaza_json_invalido(client):
    response = client.post('/api/execute/', data='{', content_type='application/json')
    assert response.status_code == 400

def test_execute_requiere_code(client):
    assert post_json(client, {}).status_code == 400

def test_execute_programa_valido(client):
    with tempfile.TemporaryDirectory() as tmp:
        with override_settings(REPORTS_ROOT=Path(tmp)):
            response = post_json(client, {'code': 'fn main() { println!("Hola API"); }'})
    data = response.json()
    assert response.status_code == 200
    assert data['success'] is True
    assert data['output'] == 'Hola API'
    assert data['errors'] == []
    assert data['symbols']
    assert 'digraph OxigenScriptAST' in data['ast_dot']

def test_execute_programa_con_error_semantico(client):
    with tempfile.TemporaryDirectory() as tmp:
        with override_settings(REPORTS_ROOT=Path(tmp)):
            response = post_json(client, {'code': 'fn main() { println!(variable_no_existe); }'})
    data = response.json()
    assert response.status_code == 200
    assert data['success'] is False
    assert data['errors'][0]['tipo'] == 'Semántico'

def test_execute_genera_reportes_fisicos(client):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        with override_settings(REPORTS_ROOT=root):
            response = post_json(client, {'code': 'fn main() { let x = 10; println!("{}", x); }'})
            assert response.status_code == 200
            assert (root/'errors'/'errores.html').exists()
            assert (root/'symbols'/'tabla_simbolos.html').exists()
            assert (root/'ast'/'ast.dot').exists()

def test_execute_respeta_limite(client):
    with override_settings(OXIGENSCRIPT_MAX_SOURCE_LENGTH=10):
        response = post_json(client, {'code': 'fn main() { println!("x"); }'})
    assert response.status_code == 413

def test_reports_404_antes_de_ejecutar(client):
    with tempfile.TemporaryDirectory() as tmp:
        with override_settings(REPORTS_ROOT=Path(tmp)):
            assert client.get('/api/reports/errors/').status_code == 404
            assert client.get('/api/reports/symbols/').status_code == 404
            assert client.get('/api/reports/ast/').status_code == 404

def test_reports_disponibles_despues_de_ejecutar(client):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        with override_settings(REPORTS_ROOT=root):
            response = post_json(client, {'code': 'fn main() { println!("reportes"); }'})
            assert response.status_code == 200
            assert client.get('/api/reports/errors/').status_code == 200
            assert client.get('/api/reports/symbols/').status_code == 200
            assert client.get('/api/reports/ast/').status_code == 200
