import json
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from interpreter.runtime.runner import run_source


def _json_error(message, status=400):
    return JsonResponse({'success': False, 'message': message}, status=status)


def _read_json_body(request):
    try:
        raw = request.body.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('El cuerpo de la solicitud debe estar codificado en UTF-8.') from exc
    if not raw.strip():
        raise ValueError('El cuerpo de la solicitud está vacío.')
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError('El cuerpo de la solicitud no contiene JSON válido.') from exc
    if not isinstance(data, dict):
        raise ValueError('El JSON de entrada debe ser un objeto.')
    return data


def _report_path(section, filename):
    return Path(settings.REPORTS_ROOT) / section / filename


@require_GET
def health(request):
    return JsonResponse({'status': 'ok', 'service': 'OxigenScript API'})


@csrf_exempt
@require_POST
def execute_code(request):
    try:
        data = _read_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc), 400)

    code = data.get('code')
    if not isinstance(code, str):
        return _json_error("El campo 'code' es obligatorio y debe ser una cadena.", 400)
    if not code.strip():
        return _json_error("El campo 'code' no puede estar vacío.", 400)

    max_length = getattr(settings, 'OXIGENSCRIPT_MAX_SOURCE_LENGTH', 500_000)
    if len(code) > max_length:
        return _json_error(f'El código fuente supera el tamaño máximo permitido de {max_length} caracteres.', 413)

    try:
        result = run_source(code, report_dir=settings.REPORTS_ROOT)
    except Exception as exc:
        return _json_error(f'Ocurrió un error interno al procesar el programa: {type(exc).__name__}.', 500)

    reports = result.get('reports', {})
    errors = reports.get('errors', [])
    response = {
        'success': len(errors) == 0,
        'output': result.get('output', ''),
        'errors': errors,
        'symbols': reports.get('symbols', []),
        'ast_dot': reports.get('ast_dot', ''),
        'report_urls': {
            'errors': '/api/reports/errors/',
            'symbols': '/api/reports/symbols/',
            'ast': '/api/reports/ast/',
        },
    }
    return JsonResponse(response, status=200, json_dumps_params={'ensure_ascii': False})


@require_GET
def errors_report(request):
    path = _report_path('errors', 'errores.html')
    if not path.exists():
        return _json_error('Todavía no se ha generado el reporte de errores.', 404)
    return FileResponse(path.open('rb'), content_type='text/html; charset=utf-8', filename='errores.html')


@require_GET
def symbols_report(request):
    path = _report_path('symbols', 'tabla_simbolos.html')
    if not path.exists():
        return _json_error('Todavía no se ha generado la tabla de símbolos.', 404)
    return FileResponse(path.open('rb'), content_type='text/html; charset=utf-8', filename='tabla_simbolos.html')


@require_GET
def ast_report(request):
    svg_path = _report_path('ast', 'ast.svg')
    dot_path = _report_path('ast', 'ast.dot')
    if svg_path.exists():
        return FileResponse(svg_path.open('rb'), content_type='image/svg+xml', filename='ast.svg')
    if dot_path.exists():
        return HttpResponse(dot_path.read_text(encoding='utf-8'), content_type='text/vnd.graphviz; charset=utf-8')
    return _json_error('Todavía no se ha generado el reporte AST.', 404)
