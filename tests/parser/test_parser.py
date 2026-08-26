import os
import sys

import pytest

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')
)
sys.path.insert(0, ROOT)

from interpreter.errors import ErrorList
from interpreter.parser.parser import parse
from interpreter.ast.nodes import *


def _parse(code):
    """Parsea sin errores esperados."""
    errors = ErrorList()
    ast = parse(code, errors)
    assert not errors.has_errors(), (
        'No se esperaban errores: '
        + str([str(e) for e in errors.get_all()])
    )
    return ast


def _parse_con_errores(code):
    """Parsea y devuelve (ast, errors)."""
    errors = ErrorList()
    ast = parse(code, errors)
    return ast, errors


# ============================================================
# DECLARACION DE VARIABLES
# ============================================================

class TestVarDeclaration:

    def test_var_con_tipo(self):
        ast = _parse('fn main() { let x: i32 = 10; }')
        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl, VarDeclaration)
        assert decl.nombre == 'x'
        assert decl.mutable is False
        assert decl.tipo == 'i32'
        assert isinstance(decl.valor, Literal)
        assert decl.valor.valor == 10

    def test_var_sin_tipo(self):
        ast = _parse('fn main() { let y = 3.14; }')
        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert decl.nombre == 'y'
        assert decl.tipo is None
        assert decl.valor.valor == 3.14

    def test_var_mutable(self):
        ast = _parse('fn main() { let mut cont: i32 = 0; }')
        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert decl.nombre == 'cont'
        assert decl.mutable is True
        assert decl.tipo == 'i32'

    def test_var_mutable_sin_tipo(self):
        ast = _parse('fn main() { let mut x = 5; }')
        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert decl.mutable is True
        assert decl.tipo is None

    def test_var_string_from(self):
        ast = _parse(
            'fn main() { let s = String::from("hola"); }'
        )
        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl.valor, StringFrom)

    def test_var_string_new(self):
        ast = _parse(
            'fn main() { let s = String::new(); }'
        )
        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl.valor, StringNew)

    def test_var_bool(self):
        ast = _parse(
            'fn main() { let f: bool = true; }'
        )
        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert decl.tipo == 'bool'
        assert isinstance(decl.valor, Literal)
        assert decl.valor.valor is True

    def test_var_tipo_arreglo(self):
        ast = _parse(
            'fn main() { let nums: [i32; 3] = [1, 2, 3]; }'
        )
        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert decl.tipo == ('array', 'i32', 3)
        assert isinstance(decl.valor, ArrayLiteral)
        assert len(decl.valor.elementos) == 3

    def test_var_con_tipo_sin_valor(self):
        ast = _parse(
            'fn main() { let x: i32; }'
        )

        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl, VarDeclaration)
        assert decl.nombre == 'x'
        assert decl.mutable is False
        assert decl.tipo == 'i32'
        assert decl.valor is None


    def test_var_mutable_con_tipo_sin_valor(self):
        ast = _parse(
            'fn main() { let mut x: i32; }'
        )

        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl, VarDeclaration)
        assert decl.nombre == 'x'
        assert decl.mutable is True
        assert decl.tipo == 'i32'
        assert decl.valor is None


    def test_var_sin_tipo_sin_valor(self):
        ast = _parse(
            'fn main() { let x; }'
        )

        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl, VarDeclaration)
        assert decl.nombre == 'x'
        assert decl.mutable is False
        assert decl.tipo is None
        assert decl.valor is None


    def test_var_mutable_sin_tipo_sin_valor(self):
        ast = _parse(
            'fn main() { let mut x; }'
        )

        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl, VarDeclaration)
        assert decl.nombre == 'x'
        assert decl.mutable is True
        assert decl.tipo is None
        assert decl.valor is None


# ============================================================
# LITERALES
# ============================================================

class TestLiterales:

    def test_tipos_de_literales(self):
        ast = _parse(
            'fn main() { '
            'let a = 10; '
            'let b = 3.14; '
            'let c = true; '
            "let d = 'x'; "
            'let e = "hola"; '
            '}'
        )

        instrucciones = ast.declaraciones[0].cuerpo.instrucciones

        assert instrucciones[0].valor.tipo == 'i32'
        assert instrucciones[1].valor.tipo == 'f64'
        assert instrucciones[2].valor.tipo == 'bool'
        assert instrucciones[3].valor.tipo == 'char'
        assert instrucciones[4].valor.tipo == 'String'


# ============================================================
# OPERADORES Y PRECEDENCIA
# ============================================================

class TestPrecedencia:

    def test_multiplicacion_antes_suma(self):
        ast = _parse('fn main() { let x = 2 + 3 * 4; }')
        expr = ast.declaraciones[0].cuerpo.instrucciones[0].valor

        # raiz debe ser +
        assert isinstance(expr, BinaryOp)
        assert expr.op == '+'
        # derecha debe ser *
        assert isinstance(expr.der, BinaryOp)
        assert expr.der.op == '*'

    def test_parentesis_cambia_precedencia(self):
        ast = _parse('fn main() { let x = (2 + 3) * 4; }')
        expr = ast.declaraciones[0].cuerpo.instrucciones[0].valor

        # raiz debe ser *
        assert isinstance(expr, BinaryOp)
        assert expr.op == '*'
        # izquierda debe ser +
        assert isinstance(expr.izq, BinaryOp)
        assert expr.izq.op == '+'

    def test_comparacion_menor_precedencia_que_aritmetica(self):
        ast = _parse('fn main() { let x = a + b > c; }')
        expr = ast.declaraciones[0].cuerpo.instrucciones[0].valor

        # raiz debe ser >
        assert isinstance(expr, Comparison)
        assert expr.op == '>'
        # izquierda debe ser +
        assert isinstance(expr.izq, BinaryOp)

    def test_logico_menor_que_comparacion(self):
        ast = _parse(
            'fn main() { let x = a > 0 && b < 10; }'
        )
        expr = ast.declaraciones[0].cuerpo.instrucciones[0].valor

        # raiz debe ser &&
        assert isinstance(expr, LogicalOp)
        assert expr.op == '&&'
        assert isinstance(expr.izq, Comparison)
        assert isinstance(expr.der, Comparison)

    def test_not_antes_que_igualdad(self):
        ast = _parse(
            'fn main() { let x = !a == b; }'
        )

        expr = ast.declaraciones[0].cuerpo.instrucciones[0].valor

        # La raíz debe ser ==
        assert isinstance(expr, Comparison)
        assert expr.op == '=='

        # La izquierda debe ser !a
        assert isinstance(expr.izq, UnaryOp)
        assert expr.izq.op == '!'

        assert isinstance(expr.izq.operando, Identifier)
        assert expr.izq.operando.nombre == 'a'

        assert isinstance(expr.der, Identifier)
        assert expr.der.nombre == 'b'

    def test_not_antes_que_and(self):
        ast = _parse(
            'fn main() { let x = !a && b; }'
        )

        expr = ast.declaraciones[0].cuerpo.instrucciones[0].valor

        # (!a) && b
        assert isinstance(expr, LogicalOp)
        assert expr.op == '&&'

        assert isinstance(expr.izq, UnaryOp)
        assert expr.izq.op == '!'

        assert isinstance(expr.izq.operando, Identifier)
        assert expr.izq.operando.nombre == 'a'

    def test_menos_unario_antes_que_multiplicacion(self):
        ast = _parse(
            'fn main() { let x = -a * b; }'
        )

        expr = ast.declaraciones[0].cuerpo.instrucciones[0].valor

        # (-a) * b
        assert isinstance(expr, BinaryOp)
        assert expr.op == '*'

        assert isinstance(expr.izq, UnaryOp)
        assert expr.izq.op == '-'

        assert isinstance(expr.izq.operando, Identifier)
        assert expr.izq.operando.nombre == 'a'
        
    def test_negacion_unaria(self):
        ast = _parse('fn main() { let x = -5; }')
        expr = ast.declaraciones[0].cuerpo.instrucciones[0].valor

        assert isinstance(expr, UnaryOp)
        assert expr.op == '-'
        assert expr.operando.valor == 5

    def test_not_logico(self):
        ast = _parse('fn main() { let x = !true; }')
        expr = ast.declaraciones[0].cuerpo.instrucciones[0].valor

        assert isinstance(expr, UnaryOp)
        assert expr.op == '!'
        assert expr.operando.valor is True

    def test_precedencia_completa(self):
        ast = _parse(
            'fn main() { '
            'let x = !a || b + c * d > e && f; '
            '}'
        )

        expr = ast.declaraciones[0].cuerpo.instrucciones[0].valor

        # El operador de menor precedencia debe quedar en la raíz.
        assert isinstance(expr, LogicalOp)
        assert expr.op == '||'

        # Lado izquierdo: !a
        assert isinstance(expr.izq, UnaryOp)
        assert expr.izq.op == '!'

        # Lado derecho debe contener &&
        assert isinstance(expr.der, LogicalOp)
        assert expr.der.op == '&&'

# ============================================================
# ASIGNACION
# ============================================================

class TestAsignacion:

    def test_asignacion_simple(self):
        ast = _parse('fn main() { let mut x = 1; x = 5; }')
        asig = ast.declaraciones[0].cuerpo.instrucciones[1]

        assert isinstance(asig, Assignment)
        assert isinstance(asig.target, Identifier)
        assert asig.target.nombre == 'x'

    def test_asignacion_compuesta(self):
        ast = _parse(
            'fn main() { let mut x = 0; '
            'x += 1; x -= 2; x *= 3; x /= 4; x %= 5; }'
        )
        instrucciones = ast.declaraciones[0].cuerpo.instrucciones

        ops = [inst.op for inst in instrucciones[1:]]
        assert ops == ['+=', '-=', '*=', '/=', '%=']

    def test_asignacion_campo(self):
        ast = _parse(
            'fn main() { p.x = 10; }'
        )
        asig = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(asig, Assignment)
        assert isinstance(asig.target, FieldAccess)

    def test_asignacion_indice(self):
        ast = _parse(
            'fn main() { nums[0] = 5; }'
        )
        asig = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(asig, Assignment)
        assert isinstance(asig.target, ArrayAccess)

    def test_asignacion_target_aritmetico_invalido(self):
        _, errors = _parse_con_errores(
            'fn main() { 1 + 2 = 10; }'
        )

        assert errors.has_errors()

        error = errors.get_all()[0]

        assert error.tipo == 'Sintáctico'
        assert 'lado izquierdo' in error.descripcion


    def test_asignacion_target_llamada_invalido(self):
        _, errors = _parse_con_errores(
            'fn main() { sumar() = 10; }'
        )

        assert errors.has_errors()


    def test_asignacion_compuesta_target_invalido(self):
        _, errors = _parse_con_errores(
            'fn main() { 5 += 2; }'
        )

        assert errors.has_errors()


    def test_asignacion_campo_anidado_valido(self):
        ast = _parse(
            'fn main() { rect.position.x = 10; }'
        )

        asig = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(asig, Assignment)
        assert isinstance(asig.target, FieldAccess)
        assert asig.target.campo == 'x'
        assert isinstance(asig.target.objeto, FieldAccess)
        assert asig.target.objeto.campo == 'position'


# ============================================================
# IF / ELSE
# ============================================================

class TestIfStmt:


    def test_if_con_parentesis_genera_error(self):
        _, errors = _parse_con_errores(
            'fn main() { '
            'if (x > 0) { '
            'println!("positivo"); '
            '} '
            '}'
        )

        assert errors.has_errors()

        error = errors.get_all()[0]

        assert error.tipo == 'Sintáctico'
        assert 'paréntesis' in error.descripcion

    def test_if_simple(self):
        ast = _parse('fn main() { if x > 0 { println!("si"); } }')
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt, IfStmt)
        assert isinstance(stmt.condicion, Comparison)
        assert isinstance(stmt.cuerpo, Block)
        assert stmt.else_branch is None

    def test_if_else(self):
        ast = _parse(
            'fn main() { '
            'if x > 0 { println!("si"); } '
            'else { println!("no"); } '
            '}'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt.else_branch, Block)

    def test_if_else_if(self):
        ast = _parse(
            'fn main() { '
            'if x > 0 { println!("pos"); } '
            'else if x < 0 { println!("neg"); } '
            'else { println!("cero"); } '
            '}'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt.else_branch, IfStmt)
        assert isinstance(stmt.else_branch.else_branch, Block)

    def test_else_if_con_parentesis_genera_error(self):
        _, errors = _parse_con_errores(
            'fn main() { '
            'if x > 0 { '
            'println!("positivo"); '
            '} '
            'else if (x < 0) { '
            'println!("negativo"); '
            '} '
            '}'
        )

        assert errors.has_errors()

        assert any(
            'paréntesis' in error.descripcion
            for error in errors.get_all()
        )

    def test_if_permite_parentesis_en_subexpresion(self):
        ast = _parse(
            'fn main() { '
            'if (a + b) > c { '
            'println!("ok"); '
            '} '
            '}'
        )

        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt, IfStmt)
        assert isinstance(stmt.condicion, Comparison)    

    def test_if_sin_parentesis_es_valido(self):
        ast = _parse(
            'fn main() { '
            'if x > 0 { '
            'println!("ok"); '
            '} '
            '}'
        )

        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt, IfStmt)

# ============================================================
# WHILE
# ============================================================

class TestWhileStmt:

    def test_while_basico(self):
        ast = _parse(
            'fn main() { let mut i = 0; '
            'while i < 10 { i += 1; } }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[1]

        assert isinstance(stmt, WhileStmt)
        assert isinstance(stmt.condicion, Comparison)
        assert isinstance(stmt.cuerpo, Block)


# ============================================================
# LOOP
# ============================================================

class TestLoopStmt:

    def test_loop_simple(self):
        ast = _parse(
            'fn main() { loop { break; } }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt, LoopStmt)
        assert stmt.etiqueta is None

    def test_loop_con_etiqueta(self):
        ast = _parse(
            "fn main() {\n"
            "    'outer: loop {\n"
            "        break 'outer;\n"
            "    }\n"
            "}"
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt, LoopStmt)
        assert stmt.etiqueta == 'outer'

    def test_loop_anidado(self):
        ast = _parse(
            "fn main() {\n"
            "    'outer: loop {\n"
            "        'inner: loop {\n"
            "            break 'outer;\n"
            "        }\n"
            "    }\n"
            "}"
        )
        outer = ast.declaraciones[0].cuerpo.instrucciones[0]
        inner = outer.cuerpo.instrucciones[0]

        assert outer.etiqueta == 'outer'
        assert inner.etiqueta == 'inner'


# ============================================================
# MATCH
# ============================================================

class TestMatchStmt:

    def test_match_basico(self):
        ast = _parse(
            'fn main() { '
            'match x { '
            '1 => println!("uno"), '
            '2 => println!("dos"), '
            '_ => println!("otro"), '
            '} }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt, MatchStmt)
        assert len(stmt.brazos) == 3

        # primer brazo: patron es literal 1
        assert isinstance(stmt.brazos[0].patron, Literal)
        assert stmt.brazos[0].patron.valor == 1

        # ultimo brazo: wildcard
        assert isinstance(stmt.brazos[2].patron, Identifier)
        assert stmt.brazos[2].patron.nombre == '_'

    def test_match_con_bloque(self):
        ast = _parse(
            'fn main() { '
            'match n { '
            '1 => { println!("uno"); }, '
            '_ => { println!("otro"); }, '
            '} }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]
        brazo = stmt.brazos[0]

        assert isinstance(brazo.cuerpo, Block)

    def test_match_sin_coma_final(self):
        ast = _parse(
            'fn main() { '
            'match x { '
            '1 => println!("uno"), '
            '_ => println!("otro") '
            '} }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert len(stmt.brazos) == 2

    def test_match_patron_expresion(self):
        ast = _parse(
            'fn main() { '
            'match x { '
            '1 + 1 => println!("dos"), '
            '_ => println!("otro"), '
            '} }'
        )

        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt, MatchStmt)
        assert len(stmt.brazos) == 2

        patron = stmt.brazos[0].patron

        assert isinstance(patron, BinaryOp)
        assert patron.op == '+'

    def test_match_patron_identificador(self):
        ast = _parse(
            'fn main() { '
            'match x { '
            'limite => println!("limite"), '
            '_ => println!("otro"), '
            '} }'
        )

        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]
        patron = stmt.brazos[0].patron

        assert isinstance(patron, Identifier)
        assert patron.nombre == 'limite'

    def test_match_sin_wildcard_genera_error(self):
        _, errors = _parse_con_errores(
            'fn main() { '
            'match x { '
            '1 => println!("uno"), '
            '2 => println!("dos"), '
            '} }'
        )

        assert errors.has_errors()

        error = errors.get_all()[0]

        assert error.tipo == 'Sintáctico'
        assert 'comodín' in error.descripcion
        assert '_' in error.descripcion

    def test_match_con_wildcard_es_valido(self):
        ast = _parse(
            'fn main() { '
            'match x { '
            '1 => println!("uno"), '
            '_ => println!("otro"), '
            '} }'
        )

        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt, MatchStmt)
        assert len(stmt.brazos) == 2


# ============================================================
# FUNCIONES
# ============================================================

class TestFunciones:

    def test_funcion_sin_retorno(self):
        ast = _parse(
            'fn saludar(nombre: String) { '
            'println!("{}", nombre); '
            '}'
        )
        fn = ast.declaraciones[0]

        assert isinstance(fn, FunctionDecl)
        assert fn.nombre == 'saludar'
        assert fn.tipo_retorno is None
        assert len(fn.params) == 1
        assert fn.params[0].nombre == 'nombre'
        assert fn.params[0].tipo == 'String'

    def test_funcion_con_retorno(self):
        ast = _parse(
            'fn sumar(a: i32, b: i32) -> i32 { '
            'return a + b; '
            '}'
        )
        fn = ast.declaraciones[0]

        assert fn.nombre == 'sumar'
        assert fn.tipo_retorno == 'i32'
        assert len(fn.params) == 2

    def test_funcion_sin_params(self):
        ast = _parse('fn main() { }')
        fn = ast.declaraciones[0]

        assert fn.nombre == 'main'
        assert fn.params == []

    def test_llamada_funcion(self):
        ast = _parse(
            'fn main() { sumar(10, 20); }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt, ExpressionStmt)
        call = stmt.expresion
        assert isinstance(call, FunctionCall)
        assert call.nombre == 'sumar'
        assert len(call.argumentos) == 2

    def test_return_vacio(self):
        ast = _parse('fn foo() { return; }')
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt, ReturnStmt)
        assert stmt.valor is None

    def test_return_valor(self):
        ast = _parse('fn foo() -> i32 { return 42; }')
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt, ReturnStmt)
        assert isinstance(stmt.valor, Literal)


# ============================================================
# STRUCTS
# ============================================================

class TestStructs:

    def test_struct_decl(self):
        ast = _parse(
            'struct Point { x: i32, y: i32, }'
        )
        s = ast.declaraciones[0]

        assert isinstance(s, StructDecl)
        assert s.nombre == 'Point'
        assert len(s.campos) == 2
        assert s.campos[0].nombre == 'x'
        assert s.campos[0].tipo == 'i32'

    def test_struct_init(self):
        ast = _parse(
            'fn main() { '
            'let p = Point { x: 10, y: 20 }; '
            '}'
        )

        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl.valor, StructInit)
        assert decl.valor.nombre == 'Point'
        assert len(decl.valor.campos) == 2

        nombre_x, valor_x = decl.valor.campos[0]
        assert nombre_x == 'x'
        assert isinstance(valor_x, Literal)
        assert valor_x.valor == 10

        nombre_y, valor_y = decl.valor.campos[1]
        assert nombre_y == 'y'
        assert isinstance(valor_y, Literal)
        assert valor_y.valor == 20

    def test_struct_anidado(self):
        ast = _parse(
            'struct Point { x: i32, y: i32 }\n'
            'struct Rect { pos: Point }\n'
            'fn main() { '
            'let r = Rect { pos: Point { x: 1, y: 2 } }; '
            '}'
        )
        decl = ast.declaraciones[2].cuerpo.instrucciones[0]
        rect = decl.valor

        assert isinstance(rect, StructInit)
        inner = rect.campos[0][1]
        assert isinstance(inner, StructInit)
        assert inner.nombre == 'Point'

    def test_field_access(self):
        ast = _parse(
            'fn main() { println!("{}", p.x); }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]
        call = stmt.expresion
        arg = call.argumentos[1]

        assert isinstance(arg, FieldAccess)
        assert arg.campo == 'x'

    def test_field_access_anidado(self):
        ast = _parse(
            'fn main() { println!("{}", r.pos.x); }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]
        arg = stmt.expresion.argumentos[1]

        # r.pos.x => FieldAccess(FieldAccess(r, pos), x)
        assert isinstance(arg, FieldAccess)
        assert arg.campo == 'x'
        assert isinstance(arg.objeto, FieldAccess)
        assert arg.objeto.campo == 'pos'


# ============================================================
# ARREGLOS Y SLICES
# ============================================================

class TestArreglos:

    def test_arreglo_literal(self):
        ast = _parse(
            'fn main() { let nums = [10, 20, 30]; }'
        )
        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl.valor, ArrayLiteral)
        assert len(decl.valor.elementos) == 3

    def test_arreglo_repetido(self):
        ast = _parse(
            'fn main() { let nums = [0; 5]; }'
        )

        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl.valor, ArrayRepeat)
        assert isinstance(decl.valor.valor, Literal)
        assert decl.valor.valor.valor == 0
        assert decl.valor.cantidad == 5

    def test_arreglo_repetido_con_expresion(self):
        ast = _parse(
            'fn main() { let nums = [1 + 2; 4]; }'
        )

        decl = ast.declaraciones[0].cuerpo.instrucciones[0]
        arreglo = decl.valor

        assert isinstance(arreglo, ArrayRepeat)
        assert isinstance(arreglo.valor, BinaryOp)
        assert arreglo.valor.op == '+'
        assert arreglo.cantidad == 4

    def test_arreglo_repetido_con_tipo(self):
        ast = _parse(
            'fn main() { let nums: [i32; 5] = [0; 5]; }'
        )

        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert decl.tipo == ('array', 'i32', 5)
        assert isinstance(decl.valor, ArrayRepeat)
        assert decl.valor.cantidad == 5
    
    def test_arreglo_vacio(self):
        ast = _parse(
            'fn main() { let v = []; }'
        )
        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl.valor, ArrayLiteral)
        assert len(decl.valor.elementos) == 0

    def test_acceso_arreglo(self):
        ast = _parse(
            'fn main() { println!("{}", nums[0]); }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]
        arg = stmt.expresion.argumentos[1]

        assert isinstance(arg, ArrayAccess)
        assert isinstance(arg.indice, Literal)

    def test_slice(self):
        ast = _parse(
            'fn main() { let s = &nums[1..4]; }'
        )
        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl.valor, SliceAccess)


# ============================================================
# CONSTRUCTORES DE STRING
# ============================================================

class TestConstructoresString:

    def test_string_from_valido(self):
        ast = _parse(
            'fn main() { let s = String::from("hola"); }'
        )

        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl.valor, StringFrom)
        assert isinstance(decl.valor.argumento, Literal)
        assert decl.valor.argumento.valor == 'hola'

    def test_string_from_conserva_tipo_string(self):
        ast = _parse(
            'fn main() { let s = String::from("hola"); }'
        )

        valor = ast.declaraciones[0].cuerpo.instrucciones[0].valor

        assert isinstance(valor, StringFrom)
        assert isinstance(valor.argumento, Literal)
        assert valor.argumento.tipo == 'String'
        
    def test_string_new_valido(self):
        ast = _parse(
            'fn main() { let s = String::new(); }'
        )

        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl.valor, StringNew)

    def test_constructor_string_invalido_con_argumento(self):
        _, errors = _parse_con_errores(
            'fn main() { let s = String::foo("hola"); }'
        )

        assert errors.has_errors()

        error = errors.get_all()[0]

        assert error.tipo == 'Sintáctico'
        assert 'String::foo' in error.descripcion

    def test_constructor_string_invalido_sin_argumentos(self):
        _, errors = _parse_con_errores(
            'fn main() { let s = String::bar(); }'
        )

        assert errors.has_errors()

        error = errors.get_all()[0]

        assert error.tipo == 'Sintáctico'
        assert 'String::bar' in error.descripcion

    def test_string_new_no_acepta_argumentos(self):
        _, errors = _parse_con_errores(
            'fn main() { let s = String::new("hola"); }'
        )

        assert errors.has_errors()

    def test_string_from_requiere_argumento(self):
        _, errors = _parse_con_errores(
            'fn main() { let s = String::from(); }'
        )

        assert errors.has_errors()

    def test_string_from_no_acepta_identificador(self):
        _, errors = _parse_con_errores(
            'fn main() { let s = String::from(x); }'
        )

        assert errors.has_errors()


    def test_string_from_no_acepta_numero(self):
        _, errors = _parse_con_errores(
            'fn main() { let s = String::from(123); }'
        )

        assert errors.has_errors()


    def test_string_from_acepta_raw_string(self):
        ast = _parse(
            r'fn main() { let s = String::from(r"C:\Users\Diego"); }'
        )

        decl = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(decl.valor, StringFrom)
        assert isinstance(decl.valor.argumento, Literal)


# ============================================================
# PRINTLN Y METODOS
# ============================================================

class TestPrintlnYMetodos:

    def test_println_simple(self):
        ast = _parse(
            'fn main() { println!("hola"); }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt.expresion, PrintlnCall)
        assert len(stmt.expresion.argumentos) == 1

    def test_println_con_formato(self):
        ast = _parse(
            'fn main() { println!("{} {}", x, y); }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert len(stmt.expresion.argumentos) == 3

    def test_method_call(self):
        ast = _parse(
            'fn main() { texto.len(); }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]

        assert isinstance(stmt.expresion, MethodCall)
        assert stmt.expresion.metodo == 'len'

    def test_method_call_con_args(self):
        ast = _parse(
            'fn main() { texto.contains("mundo"); }'
        )
        stmt = ast.declaraciones[0].cuerpo.instrucciones[0]
        call = stmt.expresion

        assert isinstance(call, MethodCall)
        assert call.metodo == 'contains'
        assert len(call.argumentos) == 1


# ============================================================
# BREAK / CONTINUE
# ============================================================

class TestTransferencia:

    def test_break_simple(self):
        ast = _parse(
            'fn main() { loop { break; } }'
        )
        loop_stmt = ast.declaraciones[0].cuerpo.instrucciones[0]
        brk = loop_stmt.cuerpo.instrucciones[0]

        assert isinstance(brk, BreakStmt)
        assert brk.etiqueta is None

    def test_break_con_label(self):
        ast = _parse(
            "fn main() {\n"
            "    'outer: loop {\n"
            "        break 'outer;\n"
            "    }\n"
            "}"
        )
        brk = (
            ast.declaraciones[0].cuerpo.instrucciones[0]
            .cuerpo.instrucciones[0]
        )

        assert isinstance(brk, BreakStmt)
        assert brk.etiqueta == 'outer'

    def test_continue_simple(self):
        ast = _parse(
            'fn main() { loop { continue; } }'
        )
        cont = (
            ast.declaraciones[0].cuerpo.instrucciones[0]
            .cuerpo.instrucciones[0]
        )

        assert isinstance(cont, ContinueStmt)
        assert cont.etiqueta is None

    def test_continue_con_label(self):
        ast = _parse(
            "fn main() {\n"
            "    'outer: loop {\n"
            "        'inner: loop {\n"
            "            continue 'outer;\n"
            "        }\n"
            "    }\n"
            "}"
        )

        outer = ast.declaraciones[0].cuerpo.instrucciones[0]
        inner = outer.cuerpo.instrucciones[0]
        cont = inner.cuerpo.instrucciones[0]

        assert isinstance(cont, ContinueStmt)
        assert cont.etiqueta == 'outer'

# ============================================================
# ERRORES SINTACTICOS
# ============================================================

class TestErrores:

    def test_falta_punto_y_coma(self):
        _, errors = _parse_con_errores(
            'fn main() { let x = 10 println!(x); }'
        )

        assert errors.has_errors()
        errores = errors.get_all()
        assert errores[0].tipo == 'Sintáctico'

    def test_eof_inesperado(self):
        _, errors = _parse_con_errores(
            'fn main() {'
        )

        assert errors.has_errors()

    def test_token_inesperado(self):
        _, errors = _parse_con_errores(
            'fn main() { let = 10; }'
        )

        assert errors.has_errors()

    def test_error_sintactico_contiene_metadata_completa(self):
        _, errors = _parse_con_errores(
            'fn main() {\n'
            '    let = 10;\n'
            '}'
        )

        assert errors.has_errors()

        error = errors.get_all()[0]

        assert error.tipo == 'Sintáctico'
        assert error.descripcion
        assert error.linea == 2
        assert error.columna > 0
        assert error.fragmento
        assert 'let = 10;' in error.fragmento

    def test_eof_contiene_fragmento(self):
        _, errors = _parse_con_errores(
            'fn main() {\n'
            '    println!("hola");'
        )

        assert errors.has_errors()

        error = errors.get_all()[0]

        assert error.tipo == 'Sintáctico'
        assert error.descripcion
        assert error.linea > 0
        assert error.columna > 0
        assert error.fragmento
        assert 'println!' in error.fragmento

    def test_recupera_multiples_errores_sintacticos(self):
        _, errors = _parse_con_errores(
            'fn main() {\n'
            '    let = 10;\n'
            '    let = 20;\n'
            '    let = 30;\n'
            '}'
        )

        errores_sintacticos = [
            error
            for error in errors.get_all()
            if error.tipo == 'Sintáctico'
        ]

        assert len(errores_sintacticos) >= 2

    def test_recuperacion_permite_continuar_analisis(self):
        ast, errors = _parse_con_errores(
            'fn main() {\n'
            '    let = 10;\n'
            '    let x = 20;\n'
            '    println!(x);\n'
            '}'
        )

        assert errors.has_errors()
        assert ast is not None

        main = ast.declaraciones[0]

        assert isinstance(main, FunctionDecl)
        assert main.nombre == 'main'

        instrucciones = main.cuerpo.instrucciones

        # La declaración inválida no entra al AST,
        # pero las instrucciones posteriores sí.
        assert len(instrucciones) == 2

        decl = instrucciones[0]

        assert isinstance(decl, VarDeclaration)
        assert decl.nombre == 'x'
        assert isinstance(decl.valor, Literal)
        assert decl.valor.valor == 20

        println_stmt = instrucciones[1]

        assert isinstance(println_stmt, ExpressionStmt)
        assert isinstance(println_stmt.expresion, PrintlnCall)

# ============================================================
# PROGRAMA COMPLETO
# ============================================================

class TestProgramaCompleto:

    def test_programa_con_todo(self):
        code = """
struct Point {
    x: i32,
    y: i32,
}

fn sumar(a: i32, b: i32) -> i32 {
    return a + b;
}

fn main() {
    let x: i32 = 10;
    let mut y = 20;
    let resultado = sumar(x, y);
    println!("{}", resultado);

    if resultado > 25 {
        println!("grande");
    } else if resultado > 15 {
        println!("mediano");
    } else {
        println!("chico");
    }

    let nums = [1, 2, 3];
    let mut i = 0;
    while i < nums.len() {
        println!("{}", nums[i]);
        i += 1;
    }

    let nombre = String::from("Ana");
    println!("{}", nombre.len());

    let p = Point { x: 1, y: 2 };
    println!("{} {}", p.x, p.y);

    match x {
        10 => println!("diez"),
        _ => println!("otro"),
    }
}
"""
        ast = _parse(code)

        assert len(ast.declaraciones) == 3

        # struct
        assert isinstance(ast.declaraciones[0], StructDecl)
        assert ast.declaraciones[0].nombre == 'Point'

        # funcion sumar
        assert isinstance(ast.declaraciones[1], FunctionDecl)
        assert ast.declaraciones[1].nombre == 'sumar'
        assert ast.declaraciones[1].tipo_retorno == 'i32'

        # funcion main
        main = ast.declaraciones[2]
        assert main.nombre == 'main'
        assert len(main.cuerpo.instrucciones) > 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
