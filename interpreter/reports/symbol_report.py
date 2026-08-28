import html
from interpreter.reports.common import CATEGORY_LABELS, html_document, type_to_string, value_to_string

class SymbolReport:
    @staticmethod
    def _symbols(symbol_table):
        if symbol_table is None:
            return []
        return symbol_table.get_all() if hasattr(symbol_table, 'get_all') else list(symbol_table)

    @classmethod
    def rows(cls, symbol_table):
        rows = []
        for index, symbol in enumerate(cls._symbols(symbol_table), start=1):
            category = getattr(symbol, 'categoria', '')
            rows.append({
                'no': index,
                'identificador': getattr(symbol, 'nombre', ''),
                'categoria': CATEGORY_LABELS.get(category, str(category)),
                'tipo': type_to_string(getattr(symbol, 'tipo', None)),
                'ambito': getattr(symbol, 'ambito', 'global'),
                'linea': getattr(symbol, 'linea', 0),
                'valor': value_to_string(getattr(symbol, 'valor', None), category=category),
            })
        return rows

    @classmethod
    def to_html(cls, symbol_table):
        rows = cls.rows(symbol_table)
        if not rows:
            return html_document(
                'Tabla de símbolos',
                '<h1>Tabla de símbolos</h1><p class="meta">OxigenScript</p>'
                '<div class="empty">No hay símbolos registrados.</div>'
            )
        table_rows = []
        for row in rows:
            table_rows.append(
                '<tr>'
                f'<td>{row["no"]}</td>'
                f'<td>{html.escape(str(row["identificador"]))}</td>'
                f'<td>{html.escape(str(row["categoria"]))}</td>'
                f'<td>{html.escape(str(row["tipo"]))}</td>'
                f'<td>{html.escape(str(row["ambito"]))}</td>'
                f'<td>{row["linea"]}</td>'
                f'<td><code>{html.escape(str(row["valor"]))}</code></td>'
                '</tr>'
            )
        body = (
            '<h1>Tabla de símbolos</h1><p class="meta">OxigenScript</p>'
            '<table><thead><tr>'
            '<th>No.</th><th>Identificador</th><th>Categoría</th><th>Tipo</th><th>Ámbito</th><th>Línea</th><th>Valor</th>'
            '</tr></thead><tbody>' + ''.join(table_rows) + '</tbody></table>'
        )
        return html_document('Tabla de símbolos', body)
