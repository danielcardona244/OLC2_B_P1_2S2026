from pathlib import Path

from interpreter.reports.ast_report import AstReport
from interpreter.reports.error_report import ErrorReport
from interpreter.reports.symbol_report import SymbolReport


class ReportManager:
    """
    Genera los reportes usando la estructura existente del proyecto:

        reports/
        ├── errors/
        ├── symbols/
        └── ast/
    """

    def __init__(self, ast=None, analyzer=None, errors=None):
        self.ast = ast
        self.analyzer = analyzer
        self.errors = errors

    def payload(self):
        symbol_table = (
            self.analyzer.symbol_table
            if self.analyzer is not None
            else None
        )

        return {
            'errors': ErrorReport.rows(self.errors),
            'symbols': SymbolReport.rows(symbol_table),
            'ast_dot': (
                AstReport().to_dot(self.ast)
                if self.ast is not None
                else ''
            ),
        }

    def write_all(self, reports_root):
        reports_root = Path(reports_root)

        errors_dir = reports_root / 'errors'
        symbols_dir = reports_root / 'symbols'
        ast_dir = reports_root / 'ast'

        errors_dir.mkdir(parents=True, exist_ok=True)
        symbols_dir.mkdir(parents=True, exist_ok=True)
        ast_dir.mkdir(parents=True, exist_ok=True)

        error_html_path = errors_dir / 'errores.html'
        symbols_html_path = symbols_dir / 'tabla_simbolos.html'
        ast_dot_path = ast_dir / 'ast.dot'
        ast_svg_path = ast_dir / 'ast.svg'

        error_html_path.write_text(
            ErrorReport.to_html(self.errors),
            encoding='utf-8',
        )

        symbol_table = (
            self.analyzer.symbol_table
            if self.analyzer is not None
            else None
        )

        symbols_html_path.write_text(
            SymbolReport.to_html(symbol_table),
            encoding='utf-8',
        )

        ast_report = AstReport()

        if self.ast is not None:
            ast_report.write_dot(
                self.ast,
                ast_dot_path,
            )

            rendered = ast_report.render_svg(
                self.ast,
                ast_svg_path,
            )
        else:
            ast_dot_path.write_text(
                'digraph OxigenScriptAST {}',
                encoding='utf-8',
            )
            rendered = None

        return {
            'errors_html': str(error_html_path),
            'symbols_html': str(symbols_html_path),
            'ast_dot': str(ast_dot_path),
            'ast_svg': (
                str(rendered)
                if rendered is not None
                else None
            ),
        }
