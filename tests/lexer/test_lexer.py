import os
import sys

import pytest


# Agregar la raíz del proyecto al path
ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')
)
sys.path.insert(0, ROOT)


from interpreter.errors import ErrorList
from interpreter.lexer.lexer import tokenize


def _tipos(tokens):
    """Devuelve solo los tipos de una lista de tokens."""
    return [token.type for token in tokens]


def _valores(tokens):
    """Devuelve solo los valores de una lista de tokens."""
    return [token.value for token in tokens]


# ============================================================
# DECLARACIÓN DE VARIABLES
# ============================================================

class TestVariables:

    def test_declaracion_con_tipo(self):
        toks = tokenize('let x: i32 = 10;')

        assert _tipos(toks) == [
            'LET',
            'IDENTIFIER',
            'COLON',
            'I32',
            'EQUALS',
            'NUMBER_INT',
            'SEMICOLON',
        ]

    def test_declaracion_mutable(self):
        toks = tokenize('let mut contador: i32 = 0;')

        assert _tipos(toks) == [
            'LET',
            'MUT',
            'IDENTIFIER',
            'COLON',
            'I32',
            'EQUALS',
            'NUMBER_INT',
            'SEMICOLON',
        ]

    def test_declaracion_float(self):
        toks = tokenize('let pi: f64 = 3.14;')

        assert _tipos(toks) == [
            'LET',
            'IDENTIFIER',
            'COLON',
            'F64',
            'EQUALS',
            'NUMBER_FLOAT',
            'SEMICOLON',
        ]

        assert toks[5].value == 3.14
        assert isinstance(toks[5].value, float)

    def test_declaracion_bool(self):
        toks = tokenize('let activo: bool = true;')

        assert _tipos(toks) == [
            'LET',
            'IDENTIFIER',
            'COLON',
            'BOOL',
            'EQUALS',
            'TRUE',
            'SEMICOLON',
        ]

    def test_declaracion_string(self):
        toks = tokenize('let nombre = String::from("Ana");')

        assert _tipos(toks) == [
            'LET',
            'IDENTIFIER',
            'EQUALS',
            'STRING_TYPE',
            'DOUBLE_COLON',
            'IDENTIFIER',
            'LPAREN',
            'STRING_LITERAL',
            'RPAREN',
            'SEMICOLON',
        ]

        assert toks[5].value == 'from'
        assert toks[7].value == 'Ana'

    def test_string_new(self):
        toks = tokenize('String::new()')

        assert _tipos(toks) == [
            'STRING_TYPE',
            'DOUBLE_COLON',
            'IDENTIFIER',
            'LPAREN',
            'RPAREN',
        ]

        assert toks[2].value == 'new'


# ============================================================
# OPERADORES
# ============================================================

class TestOperadores:

    def test_aritmeticos(self):
        toks = tokenize('5 + 3 - 2 * 4 / 1 % 2')

        assert _tipos(toks) == [
            'NUMBER_INT',
            'PLUS',
            'NUMBER_INT',
            'MINUS',
            'NUMBER_INT',
            'TIMES',
            'NUMBER_INT',
            'DIVIDE',
            'NUMBER_INT',
            'MODULO',
            'NUMBER_INT',
        ]

    def test_relacionales(self):
        toks = tokenize(
            'a == b != c > d >= e < f <= g'
        )

        assert _tipos(toks) == [
            'IDENTIFIER',
            'EQ',
            'IDENTIFIER',
            'NEQ',
            'IDENTIFIER',
            'GT',
            'IDENTIFIER',
            'GTE',
            'IDENTIFIER',
            'LT',
            'IDENTIFIER',
            'LTE',
            'IDENTIFIER',
        ]

    def test_logicos(self):
        toks = tokenize('a && b || !c')

        assert _tipos(toks) == [
            'IDENTIFIER',
            'AND',
            'IDENTIFIER',
            'OR',
            'NOT',
            'IDENTIFIER',
        ]

    def test_asignacion_compuesta(self):
        toks = tokenize(
            'x += 1; '
            'y -= 2; '
            'z *= 3; '
            'w /= 4; '
            'v %= 5;'
        )

        assert _tipos(toks) == [
            'IDENTIFIER',
            'PLUS_ASSIGN',
            'NUMBER_INT',
            'SEMICOLON',

            'IDENTIFIER',
            'MINUS_ASSIGN',
            'NUMBER_INT',
            'SEMICOLON',

            'IDENTIFIER',
            'TIMES_ASSIGN',
            'NUMBER_INT',
            'SEMICOLON',

            'IDENTIFIER',
            'DIVIDE_ASSIGN',
            'NUMBER_INT',
            'SEMICOLON',

            'IDENTIFIER',
            'MODULO_ASSIGN',
            'NUMBER_INT',
            'SEMICOLON',
        ]

    def test_operadores_dos_caracteres(self):
        toks = tokenize(
            '+= -= *= /= %= == != >= <= && || -> => .. ::'
        )

        assert _tipos(toks) == [
            'PLUS_ASSIGN',
            'MINUS_ASSIGN',
            'TIMES_ASSIGN',
            'DIVIDE_ASSIGN',
            'MODULO_ASSIGN',
            'EQ',
            'NEQ',
            'GTE',
            'LTE',
            'AND',
            'OR',
            'ARROW',
            'FAT_ARROW',
            'RANGE',
            'DOUBLE_COLON',
        ]


# ============================================================
# DELIMITADORES
# ============================================================

class TestDelimitadores:

    def test_arrow(self):
        toks = tokenize(
            'fn sumar(a: i32) -> i32 {}'
        )

        assert _tipos(toks) == [
            'FN',
            'IDENTIFIER',
            'LPAREN',
            'IDENTIFIER',
            'COLON',
            'I32',
            'RPAREN',
            'ARROW',
            'I32',
            'LBRACE',
            'RBRACE',
        ]

    def test_fat_arrow(self):
        toks = tokenize(
            '1 => println!("uno")'
        )

        assert _tipos(toks) == [
            'NUMBER_INT',
            'FAT_ARROW',
            'PRINTLN_MACRO',
            'LPAREN',
            'STRING_LITERAL',
            'RPAREN',
        ]

    def test_range(self):
        toks = tokenize('&nums[1..4]')

        assert _tipos(toks) == [
            'AMPERSAND',
            'IDENTIFIER',
            'LBRACKET',
            'NUMBER_INT',
            'RANGE',
            'NUMBER_INT',
            'RBRACKET',
        ]

    def test_double_colon(self):
        toks = tokenize(
            'String::from("hola")'
        )

        assert _tipos(toks) == [
            'STRING_TYPE',
            'DOUBLE_COLON',
            'IDENTIFIER',
            'LPAREN',
            'STRING_LITERAL',
            'RPAREN',
        ]


# ============================================================
# COMENTARIOS
# ============================================================

class TestComentarios:

    def test_linea(self):
        code = (
            'let x = 10; // esto es un comentario\n'
            'let y = 20;'
        )

        toks = tokenize(code)

        assert _tipos(toks) == [
            'LET',
            'IDENTIFIER',
            'EQUALS',
            'NUMBER_INT',
            'SEMICOLON',

            'LET',
            'IDENTIFIER',
            'EQUALS',
            'NUMBER_INT',
            'SEMICOLON',
        ]

    def test_bloque(self):
        code = (
            'let a = 1; '
            '/* comentario\n'
            'en varias lineas */ '
            'let b = 2;'
        )

        toks = tokenize(code)

        assert _tipos(toks) == [
            'LET',
            'IDENTIFIER',
            'EQUALS',
            'NUMBER_INT',
            'SEMICOLON',

            'LET',
            'IDENTIFIER',
            'EQUALS',
            'NUMBER_INT',
            'SEMICOLON',
        ]

    def test_bloque_sin_cerrar(self):
        errors = ErrorList()

        toks = tokenize(
            'let x = 10; /* comentario sin cerrar',
            errors,
        )

        errores = errors.get_all()

        assert len(errores) == 1
        assert errores[0].tipo == 'Léxico'
        assert 'sin cerrar' in errores[0].descripcion

        # El contenido posterior al inicio del comentario
        # no debe convertirse en tokens.
        assert _tipos(toks) == [
            'LET',
            'IDENTIFIER',
            'EQUALS',
            'NUMBER_INT',
            'SEMICOLON',
        ]

    def test_comentario_sin_cerrar_no_produce_tokens_extra(self):
        errors = ErrorList()

        code = (
            'let x = 10; '
            '/* comentario '
            'let y = 20; '
            'println!("{}", y);'
        )

        toks = tokenize(code, errors)

        assert _tipos(toks) == [
            'LET',
            'IDENTIFIER',
            'EQUALS',
            'NUMBER_INT',
            'SEMICOLON',
        ]

        assert len(errors.get_all()) == 1

    def test_linea_despues_comentario_multilinea(self):
        errors = ErrorList()

        code = """let x = 10;
/* comentario
   multilinea */
let y = @20;
"""

        tokenize(code, errors)

        errores = errors.get_all()

        assert len(errores) == 1

        # El @ está en la línea 4.
        assert errores[0].linea == 4


# ============================================================
# STRINGS
# ============================================================

class TestStrings:

    def test_string_simple(self):
        toks = tokenize('"Hola Mundo"')

        assert toks[0].type == 'STRING_LITERAL'
        assert toks[0].value == 'Hola Mundo'

    def test_escape_newline(self):
        toks = tokenize(r'"Hola\nRust"')

        assert toks[0].type == 'STRING_LITERAL'
        assert toks[0].value == 'Hola\nRust'

    def test_escape_backslash(self):
        toks = tokenize(
            r'"C:\\Users\\Diego"'
        )

        assert toks[0].type == 'STRING_LITERAL'
        assert toks[0].value == r'C:\Users\Diego'

    def test_escape_comillas(self):
        toks = tokenize(
            r'"El dijo: \"Hola\""'
        )

        assert toks[0].type == 'STRING_LITERAL'
        assert toks[0].value == 'El dijo: "Hola"'

    def test_raw_string(self):
        toks = tokenize(
            r'r"C:\Users\Diego"'
        )

        assert toks[0].type == 'STRING_LITERAL'
        assert toks[0].value == r'C:\Users\Diego'

    def test_raw_string_hash(self):
        toks = tokenize(
            'r#"El dijo: "Hola""#'
        )

        assert toks[0].type == 'STRING_LITERAL'
        assert toks[0].value == 'El dijo: "Hola"'

    def test_string_vacio(self):
        toks = tokenize('""')

        assert toks[0].type == 'STRING_LITERAL'
        assert toks[0].value == ''

    def test_string_con_salto_fisico_genera_error(self):
        errors = ErrorList()

        tokenize(
            '"Hola\nMundo"',
            errors,
        )

        assert errors.has_errors()


# ============================================================
# CHAR Y LABELS
# ============================================================

class TestCharYLabels:

    def test_char_literal(self):
        toks = tokenize("'a'")

        assert _tipos(toks) == [
            'CHAR_LITERAL',
        ]

        assert toks[0].value == 'a'

    def test_char_escape_newline(self):
        toks = tokenize(r"'\n'")

        assert _tipos(toks) == [
            'CHAR_LITERAL',
        ]

        assert toks[0].value == '\n'

    def test_char_invalido_dos_caracteres(self):
        errors = ErrorList()

        toks = tokenize("'ab'", errors)

        assert toks == []
        assert errors.has_errors()

        errores = errors.get_all()

        assert len(errores) == 1
        assert errores[0].tipo == 'Léxico'

        assert (
            'exactamente un carácter'
            in errores[0].descripcion
        )

    def test_char_vacio_invalido(self):
        errors = ErrorList()

        toks = tokenize("''", errors)

        assert toks == []
        assert errors.has_errors()

        errores = errors.get_all()

        assert len(errores) == 1
        assert errores[0].tipo == 'Léxico'

    def test_label(self):
        toks = tokenize(
            "'outer: loop {}"
        )

        assert _tipos(toks) == [
            'LABEL',
            'COLON',
            'LOOP',
            'LBRACE',
            'RBRACE',
        ]

        assert toks[0].value == 'outer'

    def test_label_inner(self):
        toks = tokenize(
            "break 'inner;"
        )

        assert _tipos(toks) == [
            'BREAK',
            'LABEL',
            'SEMICOLON',
        ]

        assert toks[1].value == 'inner'


# ============================================================
# PRINTLN
# ============================================================

class TestPrintln:

    def test_println_basico(self):
        toks = tokenize(
            'println!("hola");'
        )

        assert _tipos(toks) == [
            'PRINTLN_MACRO',
            'LPAREN',
            'STRING_LITERAL',
            'RPAREN',
            'SEMICOLON',
        ]

        assert toks[0].value == 'println!'

    def test_println_con_formato(self):
        toks = tokenize(
            'println!("{}", x);'
        )

        assert _tipos(toks) == [
            'PRINTLN_MACRO',
            'LPAREN',
            'STRING_LITERAL',
            'COMMA',
            'IDENTIFIER',
            'RPAREN',
            'SEMICOLON',
        ]

        assert toks[2].value == '{}'


# ============================================================
# PALABRAS RESERVADAS
# ============================================================

class TestReserved:

    def test_todas_las_reservadas(self):
        reservadas = {
            'fn': 'FN',
            'let': 'LET',
            'mut': 'MUT',
            'if': 'IF',
            'else': 'ELSE',
            'while': 'WHILE',
            'loop': 'LOOP',
            'match': 'MATCH',
            'return': 'RETURN',
            'break': 'BREAK',
            'continue': 'CONTINUE',
            'struct': 'STRUCT',
            'true': 'TRUE',
            'false': 'FALSE',
            'i32': 'I32',
            'f64': 'F64',
            'bool': 'BOOL',
            'char': 'CHAR_TYPE',
            'String': 'STRING_TYPE',
        }

        for palabra, tipo in reservadas.items():
            toks = tokenize(palabra)

            assert len(toks) == 1

            assert toks[0].type == tipo, (
                f"'{palabra}' debería generar "
                f"el token '{tipo}', pero generó "
                f"'{toks[0].type}'"
            )

    def test_case_sensitive(self):
        toks = tokenize('String string STRING')

        assert _tipos(toks) == [
            'STRING_TYPE',
            'IDENTIFIER',
            'IDENTIFIER',
        ]

    def test_identificadores_con_guion_bajo(self):
        toks = tokenize(
            '_variable variable_1 __dato'
        )

        assert _tipos(toks) == [
            'IDENTIFIER',
            'IDENTIFIER',
            'IDENTIFIER',
        ]


# ============================================================
# WILDCARD / MATCH
# ============================================================

class TestWildcard:

    def test_wildcard(self):
        toks = tokenize('_')

        assert _tipos(toks) == [
            'WILDCARD',
        ]

    def test_match_wildcard(self):
        toks = tokenize(
            '_ => println!("otro"),'
        )

        assert _tipos(toks) == [
            'WILDCARD',
            'FAT_ARROW',
            'PRINTLN_MACRO',
            'LPAREN',
            'STRING_LITERAL',
            'RPAREN',
            'COMMA',
        ]


# ============================================================
# ARREGLOS Y SLICES
# ============================================================

class TestArreglosYSlices:

    def test_arreglo(self):
        code = (
            'let numeros: [i32; 3] = '
            '[10, 20, 30];'
        )

        toks = tokenize(code)

        assert _tipos(toks) == [
            'LET',
            'IDENTIFIER',
            'COLON',
            'LBRACKET',
            'I32',
            'SEMICOLON',
            'NUMBER_INT',
            'RBRACKET',
            'EQUALS',
            'LBRACKET',
            'NUMBER_INT',
            'COMMA',
            'NUMBER_INT',
            'COMMA',
            'NUMBER_INT',
            'RBRACKET',
            'SEMICOLON',
        ]

    def test_slice(self):
        toks = tokenize(
            '&numeros[1..4]'
        )

        assert _tipos(toks) == [
            'AMPERSAND',
            'IDENTIFIER',
            'LBRACKET',
            'NUMBER_INT',
            'RANGE',
            'NUMBER_INT',
            'RBRACKET',
        ]


# ============================================================
# MATCH
# ============================================================

class TestMatch:

    def test_match_completo(self):
        code = """
match numero {
    1 => println!("uno"),
    2 => println!("dos"),
    _ => println!("otro"),
}
"""

        toks = tokenize(code)

        assert _tipos(toks) == [
            'MATCH',
            'IDENTIFIER',
            'LBRACE',

            'NUMBER_INT',
            'FAT_ARROW',
            'PRINTLN_MACRO',
            'LPAREN',
            'STRING_LITERAL',
            'RPAREN',
            'COMMA',

            'NUMBER_INT',
            'FAT_ARROW',
            'PRINTLN_MACRO',
            'LPAREN',
            'STRING_LITERAL',
            'RPAREN',
            'COMMA',

            'WILDCARD',
            'FAT_ARROW',
            'PRINTLN_MACRO',
            'LPAREN',
            'STRING_LITERAL',
            'RPAREN',
            'COMMA',

            'RBRACE',
        ]


# ============================================================
# STRUCT
# ============================================================

class TestStruct:

    def test_struct(self):
        code = """
struct Point {
    x: i32,
    y: i32,
}
"""

        toks = tokenize(code)

        assert _tipos(toks) == [
            'STRUCT',
            'IDENTIFIER',
            'LBRACE',

            'IDENTIFIER',
            'COLON',
            'I32',
            'COMMA',

            'IDENTIFIER',
            'COLON',
            'I32',
            'COMMA',

            'RBRACE',
        ]


# ============================================================
# ERRORES LÉXICOS
# ============================================================

class TestErrores:

    def test_caracter_no_reconocido(self):
        errors = ErrorList()

        tokenize(
            'let x = @100;',
            errors,
        )

        errores = errors.get_all()

        assert len(errores) == 1
        assert errores[0].tipo == 'Léxico'
        assert '@' in errores[0].descripcion

    def test_multiples_errores(self):
        errors = ErrorList()

        tokenize(
            'let x = @100 + #5;',
            errors,
        )

        errores = errors.get_all()

        assert len(errores) == 2

    def test_columna_correcta(self):
        errors = ErrorList()

        tokenize(
            'let x = @100;',
            errors,
        )

        errores = errors.get_all()

        assert len(errores) == 1

        # @ está en la columna 9 (1-indexed)
        assert errores[0].columna == 9

    def test_fragmento_correcto(self):
        errors = ErrorList()

        tokenize(
            'let x = @100;',
            errors,
        )

        error = errors.get_all()[0]

        assert error.fragmento == 'let x = @100;'

    def test_error_contiene_toda_la_informacion(self):
        errors = ErrorList()

        tokenize(
            'let total = @100;',
            errors,
        )

        error = errors.get_all()[0]

        assert error.tipo == 'Léxico'
        assert error.descripcion
        assert error.linea == 1
        assert error.columna > 0
        assert error.fragmento == 'let total = @100;'


# ============================================================
# PROGRAMA COMPLETO
# ============================================================

class TestProgramaCompleto:

    def test_funcion_main(self):
        errors = ErrorList()

        code = """fn main() {
    let x: i32 = 10;
    let y: i32 = 20;
    let resultado = x + y;
    println!("{}", resultado);
}"""

        toks = tokenize(code, errors)

        tipos = _tipos(toks)

        assert tipos[0] == 'FN'
        assert tipos[1] == 'IDENTIFIER'

        assert toks[1].value == 'main'

        assert not errors.has_errors()
        assert len(errors.get_all()) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])