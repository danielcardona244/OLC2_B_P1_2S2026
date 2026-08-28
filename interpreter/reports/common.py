import html
import json

CATEGORY_LABELS = {
    'variable': 'Variable',
    'parametro': 'Parámetro',
    'funcion': 'Función',
    'struct': 'Struct',
}

def type_to_string(tipo):
    if tipo is None:
        return '—'
    if isinstance(tipo, tuple) and len(tipo) == 3 and tipo[0] == 'array':
        element = type_to_string(tipo[1])
        return f'[{element}]' if tipo[2] is None else f'[{element}; {tipo[2]}]'
    if isinstance(tipo, tuple) and len(tipo) == 2 and tipo[0] == 'slice':
        return f'&[{type_to_string(tipo[1])}]'
    return str(tipo)

def value_to_string(value, category=None):
    if category in ('funcion', 'struct'):
        return '—'
    if value is None:
        return '—'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple, dict)):
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except TypeError:
            return str(value)
    if hasattr(value, 'linea') and hasattr(value, 'columna'):
        return '—'
    return str(value)

def html_document(title, body):
    safe_title = html.escape(str(title))
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe_title}</title>
<style>
body {{ font-family: Arial, Helvetica, sans-serif; margin: 32px; color: #1f2937; }}
h1 {{ margin-bottom: 8px; }}
.meta {{ margin-bottom: 20px; color: #4b5563; }}
table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px 10px; text-align: left; vertical-align: top; }}
th {{ background: #f3f4f6; }}
tbody tr:nth-child(even) {{ background: #f9fafb; }}
code {{ white-space: pre-wrap; overflow-wrap: anywhere; }}
.empty {{ padding: 16px; border: 1px solid #d1d5db; background: #f9fafb; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""
