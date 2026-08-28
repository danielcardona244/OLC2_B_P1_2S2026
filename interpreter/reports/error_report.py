import html
from interpreter.reports.common import html_document

class ErrorReport:
    @staticmethod
    def rows(errors):
        if errors is None:
            return []
        items = errors.get_all() if hasattr(errors, 'get_all') else list(errors)
        rows = []
        for index, error in enumerate(items, start=1):
            rows.append({
                'no': index,
                'tipo': getattr(error, 'tipo', ''),
                'descripcion': getattr(error, 'descripcion', ''),
                'linea': getattr(error, 'linea', 0),
                'columna': getattr(error, 'columna', 0),
                'fragmento': getattr(error, 'fragmento', ''),
            })
        return rows

    @classmethod
    def to_html(cls, errors):
        rows = cls.rows(errors)
        if not rows:
            return html_document(
                'Reporte de errores',
                '<h1>Reporte de errores</h1><p class="meta">OxigenScript</p>'
                '<div class="empty">No se encontraron errores.</div>'
            )
        table_rows = []
        for row in rows:
            table_rows.append(
                '<tr>'
                f'<td>{row["no"]}</td>'
                f'<td>{html.escape(str(row["tipo"]))}</td>'
                f'<td>{html.escape(str(row["descripcion"]))}</td>'
                f'<td>{row["linea"]}</td>'
                f'<td>{row["columna"]}</td>'
                f'<td><code>{html.escape(str(row["fragmento"]))}</code></td>'
                '</tr>'
            )
        body = (
            '<h1>Reporte de errores</h1><p class="meta">OxigenScript</p>'
            '<table><thead><tr>'
            '<th>No.</th><th>Tipo</th><th>Descripción</th><th>Línea</th><th>Columna</th><th>Fragmento</th>'
            '</tr></thead><tbody>' + ''.join(table_rows) + '</tbody></table>'
        )
        return html_document('Reporte de errores', body)
