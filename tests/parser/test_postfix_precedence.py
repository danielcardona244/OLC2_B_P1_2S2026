from interpreter.errors import ErrorList
from interpreter.parser.parser import parse
from interpreter.ast.nodes import (
    ArrayAccess,
    BinaryOp,
    Comparison,
    FieldAccess,
    Identifier,
    MethodCall,
    WhileStmt,
)


def _parse(code):
    errors = ErrorList()
    ast = parse(code, errors)

    assert ast is not None
    assert not errors.has_errors(), (
        "\n".join(str(error) for error in errors.get_all())
    )

    return ast


def test_len_tiene_precedencia_sobre_comparacion():
    ast = _parse(
        "fn main() { "
        "let i = 0; "
        "let nums = [1, 2, 3]; "
        "while i < nums.len() { break; } "
        "}"
    )

    while_stmt = ast.declaraciones[0].cuerpo.instrucciones[2]

    assert isinstance(while_stmt, WhileStmt)
    assert isinstance(while_stmt.condicion, Comparison)

    derecha = while_stmt.condicion.der

    assert isinstance(derecha, MethodCall)
    assert derecha.metodo == "len"
    assert isinstance(derecha.objeto, Identifier)
    assert derecha.objeto.nombre == "nums"


def test_array_access_tiene_precedencia_sobre_suma():
    ast = _parse(
        "fn main() { "
        "let nums = [10, 20, 30]; "
        "let x = nums[0] + 1; "
        "}"
    )

    expr = ast.declaraciones[0].cuerpo.instrucciones[1].valor

    assert isinstance(expr, BinaryOp)
    assert expr.op == "+"
    assert isinstance(expr.izq, ArrayAccess)


def test_field_access_tiene_precedencia_sobre_suma():
    ast = _parse(
        "struct Point { x: i32 } "
        "fn main() { "
        "let p = Point { x: 10 }; "
        "let x = p.x + 1; "
        "}"
    )

    expr = ast.declaraciones[1].cuerpo.instrucciones[1].valor

    assert isinstance(expr, BinaryOp)
    assert expr.op == "+"
    assert isinstance(expr.izq, FieldAccess)


def test_metodos_encadenados_se_agrupan_correctamente():
    ast = _parse(
        'fn main() { '
        'let texto = String::from("Hola"); '
        'let n = texto.to_uppercase().len(); '
        '}'
    )

    expr = ast.declaraciones[0].cuerpo.instrucciones[1].valor

    assert isinstance(expr, MethodCall)
    assert expr.metodo == "len"
    assert isinstance(expr.objeto, MethodCall)
    assert expr.objeto.metodo == "to_uppercase"
