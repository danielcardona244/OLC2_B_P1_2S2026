import shutil
from pathlib import Path
import pytest

from interpreter.errors import ErrorList
from interpreter.parser.parser import parse
from interpreter.semantic.analyzer import SemanticAnalyzer
from interpreter.runtime.runner import run_source
from interpreter.reports.ast_report import AstReport
from interpreter.reports.error_report import ErrorReport
from interpreter.reports.symbol_report import SymbolReport

ROOT = Path(__file__).resolve().parents[2]
AUXILIAR = ROOT / 'tests' / 'fixtures' / 'prueba_auxiliar.ox'

def _semantic(code):
    errors = ErrorList()
    ast = parse(code, errors)
    analyzer = None
    if ast is not None:
        analyzer = SemanticAnalyzer(errors=errors, source_code=code)
        analyzer.analyze(ast)
    return ast, analyzer, errors

class TestErrorReport:
    def test_error_rows_incluye_campos_obligatorios(self):
        errors = ErrorList()
        errors.add('Léxico', "Carácter no reconocido '@'.", 3, 15, 'let total = @100;')
        rows = ErrorReport.rows(errors)
        assert len(rows) == 1
        assert rows[0]['tipo'] == 'Léxico'
        assert rows[0]['linea'] == 3
        assert rows[0]['columna'] == 15
        assert rows[0]['fragmento'] == 'let total = @100;'

    def test_error_html_es_tabla(self):
        errors = ErrorList()
        errors.add('Semántico', 'Error de prueba.', 1, 2, 'x')
        html = ErrorReport.to_html(errors)
        assert '<table>' in html
        assert 'Descripción' in html
        assert 'Fragmento' in html
        assert 'Error de prueba.' in html

    def test_error_html_vacio(self):
        assert 'No se encontraron errores' in ErrorReport.to_html(ErrorList())

class TestSymbolReport:
    def test_symbol_rows_tiene_columnas_del_enunciado(self):
        _, analyzer, errors = _semantic(
            'fn sumar(a: i32, b: i32) -> i32 { return a + b; } '
            'fn main() { let x: i32 = 10; }'
        )
        assert not errors.has_errors()
        rows = SymbolReport.rows(analyzer.symbol_table)
        assert rows
        assert set(rows[0].keys()) == {
            'no', 'identificador', 'categoria', 'tipo', 'ambito', 'linea', 'valor'
        }

    def test_symbol_report_incluye_funcion_parametro_variable(self):
        _, analyzer, errors = _semantic(
            'fn sumar(a: i32) -> i32 { let x: i32 = 10; return a + x; } '
            'fn main() { }'
        )
        assert not errors.has_errors()
        names = {row['identificador'] for row in SymbolReport.rows(analyzer.symbol_table)}
        assert {'sumar', 'a', 'x'} <= names

    def test_symbol_report_convierte_tipo_array(self):
        _, analyzer, errors = _semantic(
            'fn main() { let nums: [i32; 3] = [1, 2, 3]; }'
        )
        assert not errors.has_errors()
        rows = SymbolReport.rows(analyzer.symbol_table)
        nums = next(row for row in rows if row['identificador'] == 'nums')
        assert nums['tipo'] == '[i32; 3]'

    def test_symbol_html_tiene_encabezados(self):
        _, analyzer, errors = _semantic('fn main() { let x = 10; }')
        assert not errors.has_errors()
        html = SymbolReport.to_html(analyzer.symbol_table)
        assert 'Identificador' in html
        assert 'Categoría' in html
        assert 'Ámbito' in html
        assert 'Valor' in html

class TestAstReport:
    def test_ast_dot_es_graphviz_valido_basico(self):
        ast, _, errors = _semantic('fn main() { let x = 10; println!("{}", x); }')
        assert not errors.has_errors()
        dot = AstReport().to_dot(ast)
        assert dot.startswith('digraph OxigenScriptAST')
        assert 'Program' in dot
        assert 'FunctionDecl' in dot
        assert 'VarDeclaration' in dot
        assert 'PrintlnCall' in dot
        assert '->' in dot

    def test_ast_dot_incluye_operador(self):
        ast, _, errors = _semantic('fn main() { let x = 1 + 2 * 3; }')
        assert not errors.has_errors()
        dot = AstReport().to_dot(ast)
        assert 'BinaryOp' in dot
        assert 'op=+' in dot
        assert 'op=*' in dot

    def test_ast_escribe_archivo_dot(self, tmp_path):
        ast, _, errors = _semantic('fn main() { let x = 10; }')
        assert not errors.has_errors()
        path = AstReport().write_dot(ast, tmp_path / 'ast.dot')
        assert path.exists()
        assert 'digraph OxigenScriptAST' in path.read_text(encoding='utf-8')

    def test_ast_render_svg_si_graphviz_esta_instalado(self, tmp_path):
        if shutil.which('dot') is None:
            pytest.skip('Graphviz no está instalado en el sistema.')
        ast, _, errors = _semantic('fn main() { let x = 10; }')
        assert not errors.has_errors()
        path = AstReport().render_svg(ast, tmp_path / 'ast.svg')
        assert path is not None
        assert path.exists()
        assert '<svg' in path.read_text(encoding='utf-8')

class TestReportManager:
    def test_payload_listo_para_api(self):
        result = run_source('fn main() { println!("hola"); }')
        reports = result['reports']
        assert set(reports.keys()) == {'errors', 'symbols', 'ast_dot'}
        assert reports['errors'] == []
        assert reports['symbols']
        assert 'digraph' in reports['ast_dot']

    def test_pipeline_con_error_genera_reporte(self):
        result = run_source('fn main() { println!(x); }')
        assert result['errors'].has_errors()
        assert result['reports']['errors']
        assert result['reports']['errors'][0]['tipo'] == 'Semántico'

    def test_write_all_genera_html_y_dot(self, tmp_path):
        result = run_source(
            'fn main() { let x = 10; println!("{}", x); }',
            report_dir=tmp_path,
        )
        assert not result['errors'].has_errors()
        paths = result['report_files']
        assert Path(paths['errors_html']).exists()
        assert Path(paths['symbols_html']).exists()
        assert Path(paths['ast_dot']).exists()
        assert Path(paths['errors_html']).parent.name == 'errors'
        assert Path(paths['symbols_html']).parent.name == 'symbols'
        assert Path(paths['ast_dot']).parent.name == 'ast'
        if shutil.which('dot') is not None:
            assert paths['ast_svg'] is not None
            assert Path(paths['ast_svg']).exists()

    def test_archivo_auxiliar_genera_reportes(self):
        assert AUXILIAR.exists()
        result = run_source(AUXILIAR.read_text(encoding='utf-8'))
        assert not result['errors'].has_errors()
        reports = result['reports']
        assert reports['errors'] == []
        assert len(reports['symbols']) > 10
        assert 'Program' in reports['ast_dot']
        assert 'FunctionDecl' in reports['ast_dot']
        assert 'StructDecl' in reports['ast_dot']
