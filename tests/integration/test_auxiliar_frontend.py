from pathlib import Path

from interpreter.errors import ErrorList
from interpreter.parser.parser import parse
from interpreter.semantic.analyzer import SemanticAnalyzer
from interpreter.ast.nodes import Block


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'prueba_auxiliar.ox'


def _semantic(code):
    errors = ErrorList()
    ast = parse(code, errors)

    analyzer = SemanticAnalyzer(
        errors=errors,
        source_code=code
    )
    analyzer.analyze(ast)

    return ast, analyzer, errors


def test_bloque_independiente_se_parsea():
    code = (
        'fn main() { '
        'let exterior = 10; '
        '{ let interior = 20; println!(exterior, interior); } '
        'println!(exterior); '
        '}'
    )

    ast, _, errors = _semantic(code)

    assert not errors.has_errors()
    cuerpo = ast.declaraciones[0].cuerpo
    assert isinstance(cuerpo.instrucciones[1], Block)


def test_bloque_independiente_respeta_scope():
    _, _, errors = _semantic(
        'fn main() { '
        '{ let interior = 20; println!(interior); } '
        'println!(interior); '
        '}'
    )

    assert any(
        error.tipo == 'Semántico'
        and 'interior' in error.descripcion
        and 'no ha sido declarada' in error.descripcion
        for error in errors.get_all()
    )


def test_defaults_primitivos_del_auxiliar():
    _, analyzer, errors = _semantic(
        'fn main() { '
        'let contador: i32; '
        'let promedio: f64; '
        'let activo: bool; '
        'let mensaje: String; '
        'println!(contador, promedio, activo, mensaje); '
        '}'
    )

    assert not errors.has_errors()

    env = analyzer.function_envs['main']
    assert env.lookup('contador').valor == 0
    assert env.lookup('promedio').valor == 0.0
    assert env.lookup('activo').valor is False
    assert env.lookup('mensaje').valor == ''


def test_default_inmutable_ya_cuenta_como_inicializacion():
    _, _, errors = _semantic(
        'fn main() { '
        'let contador: i32; '
        'contador = 10; '
        '}'
    )

    assert any(
        error.tipo == 'Semántico'
        and 'contador' in error.descripcion
        and 'inmutable' in error.descripcion
        for error in errors.get_all()
    )


def test_archivo_auxiliar_frontend_completo_sin_errores():
    code = FIXTURE.read_text(encoding='utf-8')

    ast, _, errors = _semantic(code)

    assert ast is not None
    assert not errors.has_errors(), '\n'.join(
        str(error)
        for error in errors.get_all()
    )
