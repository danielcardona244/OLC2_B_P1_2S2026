from interpreter.errors import ErrorList
from interpreter.parser.parser import parse

from interpreter.semantic.analyzer import (
    SemanticAnalyzer,
    analyze,
)


def _semantic(code):
    errors = ErrorList()

    ast = parse(
        code,
        errors
    )

    assert ast is not None

    analyzer = SemanticAnalyzer(
        errors=errors,
        source_code=code
    )

    analyzer.analyze(ast)

    return ast, analyzer, errors


class TestGlobalSymbols:

    def test_registra_funcion_main(self):
        _, analyzer, errors = _semantic(
            'fn main() { }'
        )

        assert not errors.has_errors()

        symbol = analyzer.global_env.lookup_local('main')

        assert symbol is not None
        assert symbol.nombre == 'main'
        assert symbol.categoria == 'funcion'
        assert symbol.tipo is None


    def test_registra_funcion_con_retorno(self):
        _, analyzer, errors = _semantic(
            'fn sumar(a: i32, b: i32) -> i32 { '
            'return a + b; '
            '} '
            'fn main() { }'
        )

        assert not errors.has_errors()

        symbol = analyzer.global_env.lookup_local('sumar')

        assert symbol is not None
        assert symbol.categoria == 'funcion'
        assert symbol.tipo == 'i32'


    def test_registra_struct(self):
        _, analyzer, errors = _semantic(
            'struct Point { '
            'x: i32, '
            'y: i32 '
            '} '
            'fn main() { }'
        )

        assert not errors.has_errors()

        symbol = analyzer.global_env.lookup_local('Point')

        assert symbol is not None
        assert symbol.categoria == 'struct'
        assert symbol.tipo == 'Point'


    def test_tabla_contiene_funciones_structs_y_parametros(self):
        _, analyzer, errors = _semantic(
            'struct Point { x: i32 } '
            'fn sumar(a: i32, b: i32) -> i32 { '
            'return a + b; '
            '} '
            'fn main() { }'
        )

        assert not errors.has_errors()

        symbols = analyzer.symbol_table.get_all()

        assert len(symbols) == 5

        categorias = [
            symbol.categoria
            for symbol in symbols
        ]

        assert categorias == [
            'struct',
            'funcion',
            'funcion',
            'parametro',
            'parametro'
        ]

        assert symbols[0].nombre == 'Point'
        assert symbols[0].ambito == 'global'

        assert symbols[1].nombre == 'sumar'
        assert symbols[1].ambito == 'global'

        assert symbols[2].nombre == 'main'
        assert symbols[2].ambito == 'global'

        assert symbols[3].nombre == 'a'
        assert symbols[3].ambito == 'sumar'

        assert symbols[4].nombre == 'b'
        assert symbols[4].ambito == 'sumar'


class TestMain:

    def test_programa_con_main_es_valido(self):
        _, _, errors = _semantic(
            'fn main() { }'
        )

        assert not errors.has_errors()


    def test_programa_sin_main_genera_error(self):
        _, _, errors = _semantic(
            'fn saludar() { }'
        )

        assert errors.has_errors()

        semantic_errors = [
            error
            for error in errors.get_all()
            if error.tipo == 'Semántico'
        ]

        assert len(semantic_errors) >= 1

        error = semantic_errors[0]

        assert 'main' in error.descripcion
        assert error.linea > 0
        assert error.columna > 0
        assert error.fragmento


    def test_dos_main_generan_error(self):
        _, _, errors = _semantic(
            'fn main() { } '
            'fn main() { }'
        )

        semantic_errors = [
            error
            for error in errors.get_all()
            if error.tipo == 'Semántico'
        ]

        assert len(semantic_errors) >= 1

        assert any(
            'main' in error.descripcion
            for error in semantic_errors
        )


class TestDuplicadosGlobales:

    def test_funcion_duplicada_genera_error(self):
        _, _, errors = _semantic(
            'fn saludar() { } '
            'fn saludar() { } '
            'fn main() { }'
        )

        semantic_errors = [
            error
            for error in errors.get_all()
            if error.tipo == 'Semántico'
        ]

        assert len(semantic_errors) >= 1

        assert any(
            'saludar' in error.descripcion
            for error in semantic_errors
        )


    def test_struct_duplicado_genera_error(self):
        _, _, errors = _semantic(
            'struct Point { x: i32 } '
            'struct Point { y: i32 } '
            'fn main() { }'
        )

        semantic_errors = [
            error
            for error in errors.get_all()
            if error.tipo == 'Semántico'
        ]

        assert len(semantic_errors) >= 1

        assert any(
            'Point' in error.descripcion
            for error in semantic_errors
        )


class TestAnalyzeHelper:

    def test_funcion_helper_analyze(self):
        code = 'fn main() { }'

        errors = ErrorList()
        ast = parse(code, errors)

        analyzer = analyze(
            ast,
            errors=errors,
            source_code=code
        )

        assert analyzer.global_env.lookup('main') is not None
        assert not errors.has_errors()


class TestFunctionScopes:

    def test_crea_entorno_para_main(self):
        _, analyzer, errors = _semantic(
            'fn main() { }'
        )

        assert not errors.has_errors()

        assert 'main' in analyzer.function_envs

        main_env = analyzer.function_envs['main']

        assert main_env.nombre == 'main'
        assert main_env.padre is analyzer.global_env


    def test_parametros_se_registran_en_funcion(self):
        _, analyzer, errors = _semantic(
            'fn sumar(a: i32, b: i32) -> i32 { '
            'return a + b; '
            '} '
            'fn main() { }'
        )

        assert not errors.has_errors()

        env = analyzer.function_envs['sumar']

        a = env.lookup_local('a')
        b = env.lookup_local('b')

        assert a is not None
        assert b is not None

        assert a.categoria == 'parametro'
        assert b.categoria == 'parametro'

        assert a.tipo == 'i32'
        assert b.tipo == 'i32'


    def test_parametros_no_existen_en_global(self):
        _, analyzer, errors = _semantic(
            'fn sumar(a: i32) -> i32 { '
            'return a; '
            '} '
            'fn main() { }'
        )

        assert not errors.has_errors()

        assert analyzer.global_env.lookup_local('a') is None


    def test_parametro_duplicado_genera_error(self):
        _, _, errors = _semantic(
            'fn sumar(a: i32, a: i32) -> i32 { '
            'return a; '
            '} '
            'fn main() { }'
        )

        semantic_errors = [
            error
            for error in errors.get_all()
            if error.tipo == 'Semántico'
        ]

        assert len(semantic_errors) >= 1

        assert any(
            'a' in error.descripcion
            for error in semantic_errors
        )


class TestVariables:

    def test_variable_con_tipo_explicito(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let x: i32 = 10; '
            '}'
        )

        assert not errors.has_errors()

        env = analyzer.function_envs['main']

        x = env.lookup_local('x')

        assert x is not None
        assert x.tipo == 'i32'
        assert x.categoria == 'variable'
        assert x.mutable is False
        assert x.valor == 10


    def test_variable_infiere_i32(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let x = 10; '
            '}'
        )

        assert not errors.has_errors()

        x = analyzer.function_envs[
            'main'
        ].lookup_local('x')

        assert x.tipo == 'i32'


    def test_variable_infiere_f64(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let pi = 3.14; '
            '}'
        )

        assert not errors.has_errors()

        pi = analyzer.function_envs[
            'main'
        ].lookup_local('pi')

        assert pi.tipo == 'f64'


    def test_variable_infiere_bool(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let flag = true; '
            '}'
        )

        assert not errors.has_errors()

        flag = analyzer.function_envs[
            'main'
        ].lookup_local('flag')

        assert flag.tipo == 'bool'


    def test_variable_infiere_char(self):
        _, analyzer, errors = _semantic(
            "fn main() { "
            "let letra = 'a'; "
            "}"
        )

        assert not errors.has_errors()

        letra = analyzer.function_envs[
            'main'
        ].lookup_local('letra')

        assert letra.tipo == 'char'


    def test_variable_infiere_string_literal(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let texto = "hola"; '
            '}'
        )

        assert not errors.has_errors()

        texto = analyzer.function_envs[
            'main'
        ].lookup_local('texto')

        assert texto.tipo == 'String'


    def test_variable_infiere_string_from(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let texto = String::from("hola"); '
            '}'
        )

        assert not errors.has_errors()

        texto = analyzer.function_envs[
            'main'
        ].lookup_local('texto')

        assert texto.tipo == 'String'
        assert texto.valor == 'hola'


    def test_variable_infiere_string_new(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let texto = String::new(); '
            '}'
        )

        assert not errors.has_errors()

        texto = analyzer.function_envs[
            'main'
        ].lookup_local('texto')

        assert texto.tipo == 'String'
        assert texto.valor == ''


    def test_variable_mutable_se_registra(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let mut x: i32 = 10; '
            '}'
        )

        assert not errors.has_errors()

        x = analyzer.function_envs[
            'main'
        ].lookup_local('x')

        assert x.mutable is True


    def test_tipo_incompatible_genera_error(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let edad: i32 = "veinte"; '
            '}'
        )

        semantic_errors = [
            error
            for error in errors.get_all()
            if error.tipo == 'Semántico'
        ]

        assert len(semantic_errors) >= 1

        error = semantic_errors[0]

        assert 'String' in error.descripcion
        assert 'i32' in error.descripcion


    def test_shadowing_mismo_scope_es_valido(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let x: i32 = 10; '
            'let x: f64 = 3.14; '
            '}'
        )

        assert not errors.has_errors()

        env = analyzer.function_envs['main']

        x = env.lookup_local('x')

        # La segunda declaración es la visible.
        assert x.tipo == 'f64'
        assert x.valor == 3.14


    def test_tabla_conserva_variables_sombreadas(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let x: i32 = 10; '
            'let x: f64 = 3.14; '
            '}'
        )

        assert not errors.has_errors()

        variables_x = [
            symbol
            for symbol in analyzer.symbol_table.get_all()
            if symbol.nombre == 'x'
            and symbol.categoria == 'variable'
        ]

        assert len(variables_x) == 2

        assert variables_x[0].tipo == 'i32'
        assert variables_x[1].tipo == 'f64'


    def test_variable_local_no_existe_en_global(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let local = 10; '
            '}'
        )

        assert not errors.has_errors()

        assert (
            analyzer.global_env.lookup_local('local')
            is None
        )


class TestExpressionTypes:

    def test_operadores_numericos_i32(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let suma = 10 + 2; '
            'let resta = 10 - 2; '
            'let mult = 10 * 2; '
            'let div = 10 / 2; '
            'let mod = 10 % 3; '
            '}'
        )

        assert not errors.has_errors()

        env = analyzer.function_envs['main']

        assert env.lookup('suma').tipo == 'i32'
        assert env.lookup('resta').tipo == 'i32'
        assert env.lookup('mult').tipo == 'i32'
        assert env.lookup('div').tipo == 'i32'
        assert env.lookup('mod').tipo == 'i32'


    def test_promocion_i32_f64(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let resultado = 10 + 2.5; '
            '}'
        )

        assert not errors.has_errors()

        resultado = analyzer.function_envs[
            'main'
        ].lookup('resultado')

        assert resultado.tipo == 'f64'


    def test_suma_string(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let resultado = "Hola " + "Mundo"; '
            '}'
        )

        assert not errors.has_errors()

        resultado = analyzer.function_envs[
            'main'
        ].lookup('resultado')

        assert resultado.tipo == 'String'


    def test_multiplicacion_string_i32(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let resultado = "ha" * 3; '
            '}'
        )

        assert not errors.has_errors()

        resultado = analyzer.function_envs[
            'main'
        ].lookup('resultado')

        assert resultado.tipo == 'String'


    def test_multiplicacion_i32_string(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let resultado = 3 * "ha"; '
            '}'
        )

        assert not errors.has_errors()

        resultado = analyzer.function_envs[
            'main'
        ].lookup('resultado')

        assert resultado.tipo == 'String'


    def test_aritmetica_incompatible_genera_error(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x = 10 + "hola"; '
            '}'
        )

        semantic_errors = [
            error
            for error in errors.get_all()
            if error.tipo == 'Semántico'
        ]

        assert len(semantic_errors) >= 1

        assert any(
            '+' in error.descripcion
            and 'i32' in error.descripcion
            and 'String' in error.descripcion
            for error in semantic_errors
        )


    def test_menos_unario_numerico(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let x = -10; '
            'let y = -3.14; '
            '}'
        )

        assert not errors.has_errors()

        env = analyzer.function_envs['main']

        assert env.lookup('x').tipo == 'i32'
        assert env.lookup('y').tipo == 'f64'


    def test_menos_unario_invalido(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x = -true; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and '-' in error.descripcion
            for error in errors.get_all()
        )


    def test_comparacion_devuelve_bool(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let x = 10 > 5; '
            'let y = 10 == 10.0; '
            '}'
        )

        assert not errors.has_errors()

        env = analyzer.function_envs['main']

        assert env.lookup('x').tipo == 'bool'
        assert env.lookup('y').tipo == 'bool'


    def test_comparacion_incompatible(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x = true > 10; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and '>' in error.descripcion
            for error in errors.get_all()
        )


    def test_and_or_booleanos(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let x = true && false; '
            'let y = true || false; '
            '}'
        )

        assert not errors.has_errors()

        env = analyzer.function_envs['main']

        assert env.lookup('x').tipo == 'bool'
        assert env.lookup('y').tipo == 'bool'


    def test_logico_binario_incompatible(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x = true && 10; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and '&&' in error.descripcion
            for error in errors.get_all()
        )


    def test_not_booleano(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let x = !true; '
            '}'
        )

        assert not errors.has_errors()

        x = analyzer.function_envs[
            'main'
        ].lookup('x')

        assert x.tipo == 'bool'


    def test_not_invalido(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x = !10; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and '!' in error.descripcion
            for error in errors.get_all()
        )


class TestUndeclaredIdentifiers:

    def test_variable_no_declarada_en_inicializacion(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x = noExiste + 1; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'noExiste' in error.descripcion
            for error in errors.get_all()
        )


    def test_variable_no_declarada_en_println(self):
        _, _, errors = _semantic(
            'fn main() { '
            'println!(noExiste); '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'noExiste' in error.descripcion
            for error in errors.get_all()
        )


class TestControlConditions:

    def test_if_condicion_bool_valida(self):
        _, _, errors = _semantic(
            'fn main() { '
            'if 10 > 5 { '
            'let x = 1; '
            '} '
            '}'
        )

        assert not errors.has_errors()


    def test_if_condicion_no_bool_genera_error(self):
        _, _, errors = _semantic(
            'fn main() { '
            'if 10 { '
            'let x = 1; '
            '} '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'condición' in error.descripcion
            and 'bool' in error.descripcion
            for error in errors.get_all()
        )


    def test_while_condicion_bool_valida(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let i = 0; '
            'while i < 10 { '
            'let x = 1; '
            '} '
            '}'
        )

        assert not errors.has_errors()


    def test_while_condicion_no_bool_genera_error(self):
        _, _, errors = _semantic(
            'fn main() { '
            'while 10 { '
            '} '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'while' in error.descripcion
            and 'bool' in error.descripcion
            for error in errors.get_all()
        )


class TestAssignments:

    def test_asignacion_variable_mutable_valida(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut x: i32 = 10; '
            'x = 20; '
            '}'
        )

        assert not errors.has_errors()


    def test_asignacion_variable_inmutable_genera_error(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x: i32 = 10; '
            'x = 20; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'x' in error.descripcion
            and 'inmutable' in error.descripcion
            for error in errors.get_all()
        )


    def test_asignacion_variable_no_declarada(self):
        _, _, errors = _semantic(
            'fn main() { '
            'x = 20; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'x' in error.descripcion
            and 'no ha sido declarada' in error.descripcion
            for error in errors.get_all()
        )


    def test_asignacion_tipo_incompatible(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut x: i32 = 10; '
            'x = "hola"; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'i32' in error.descripcion
            and 'String' in error.descripcion
            for error in errors.get_all()
        )


    def test_asignacion_con_expresion_valida(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut x: i32 = 10; '
            'x = 20 + 5; '
            '}'
        )

        assert not errors.has_errors()


    def test_asignacion_rhs_variable_no_declarada(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut x: i32 = 10; '
            'x = noExiste + 1; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'noExiste' in error.descripcion
            for error in errors.get_all()
        )


class TestCompoundAssignments:

    def test_operadores_compuestos_i32_validos(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut x: i32 = 100; '
            'x += 5; '
            'x -= 2; '
            'x *= 3; '
            'x /= 4; '
            'x %= 5; '
            '}'
        )

        assert not errors.has_errors()


    def test_compuesta_variable_inmutable(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x: i32 = 10; '
            'x += 5; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'x' in error.descripcion
            and 'inmutable' in error.descripcion
            for error in errors.get_all()
        )


    def test_compuesta_variable_no_declarada(self):
        _, _, errors = _semantic(
            'fn main() { '
            'x += 5; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'x' in error.descripcion
            and 'no ha sido declarada' in error.descripcion
            for error in errors.get_all()
        )


    def test_compuesta_operacion_incompatible(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut x: i32 = 10; '
            'x += "hola"; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and '+' in error.descripcion
            and 'String' in error.descripcion
            for error in errors.get_all()
        )


    def test_compuesta_promocion_no_cabe_en_variable(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut x: i32 = 10; '
            'x += 2.5; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'f64' in error.descripcion
            and 'i32' in error.descripcion
            for error in errors.get_all()
        )


    def test_compuesta_f64_valida(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut x: f64 = 10.0; '
            'x += 2.5; '
            '}'
        )

        assert not errors.has_errors()


class TestFunctionCalls:

    def test_llamada_funcion_retorna_tipo(self):
        _, analyzer, errors = _semantic(
            'fn sumar(a: i32, b: i32) -> i32 { '
            'return a + b; '
            '} '
            'fn main() { '
            'let resultado = sumar(10, 20); '
            '}'
        )

        assert not errors.has_errors()

        resultado = analyzer.function_envs[
            'main'
        ].lookup('resultado')

        assert resultado.tipo == 'i32'


    def test_llamada_funcion_declarada_despues(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let resultado = sumar(10, 20); '
            '} '
            'fn sumar(a: i32, b: i32) -> i32 { '
            'return a + b; '
            '}'
        )

        assert not errors.has_errors()

        resultado = analyzer.function_envs[
            'main'
        ].lookup('resultado')

        assert resultado.tipo == 'i32'


    def test_funcion_no_declarada(self):
        _, _, errors = _semantic(
            'fn main() { '
            'saludar(); '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'saludar' in error.descripcion
            and 'no ha sido declarada' in error.descripcion
            for error in errors.get_all()
        )


    def test_cantidad_argumentos_incorrecta(self):
        _, _, errors = _semantic(
            'fn suma(a: i32, b: i32) { '
            '} '
            'fn main() { '
            'suma(10); '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'suma' in error.descripcion
            and '2' in error.descripcion
            and '1' in error.descripcion
            for error in errors.get_all()
        )


    def test_demasiados_argumentos(self):
        _, _, errors = _semantic(
            'fn suma(a: i32, b: i32) { '
            '} '
            'fn main() { '
            'suma(10, 20, 30); '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'suma' in error.descripcion
            for error in errors.get_all()
        )


    def test_tipo_argumento_incorrecto(self):
        _, _, errors = _semantic(
            'fn mostrar(valor: i32) { '
            '} '
            'fn main() { '
            'mostrar("hola"); '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'mostrar' in error.descripcion
            and 'i32' in error.descripcion
            and 'String' in error.descripcion
            for error in errors.get_all()
        )


    def test_funcion_sin_retorno_como_sentencia(self):
        _, _, errors = _semantic(
            'fn saludar(nombre: String) { '
            'println!(nombre); '
            '} '
            'fn main() { '
            'saludar(String::from("Ana")); '
            '}'
        )

        assert not errors.has_errors()


    def test_argumento_puede_ser_expresion(self):
        _, _, errors = _semantic(
            'fn mostrar(valor: i32) { '
            '} '
            'fn main() { '
            'mostrar(10 + 20); '
            '}'
        )

        assert not errors.has_errors()


    def test_llamada_recursiva_es_valida(self):
        _, _, errors = _semantic(
            'fn identidad(x: i32) -> i32 { '
            'return identidad(x); '
            '} '
            'fn main() { '
            'let y = identidad(10); '
            '}'
        )

        assert not errors.has_errors()


class TestReturns:

    def test_return_tipo_correcto(self):
        _, _, errors = _semantic(
            'fn obtener() -> i32 { '
            'return 10; '
            '} '
            'fn main() { }'
        )

        assert not errors.has_errors()


    def test_return_expresion_correcta(self):
        _, _, errors = _semantic(
            'fn sumar(a: i32, b: i32) -> i32 { '
            'return a + b; '
            '} '
            'fn main() { }'
        )

        assert not errors.has_errors()


    def test_return_tipo_incorrecto(self):
        _, _, errors = _semantic(
            'fn obtener() -> i32 { '
            'return "hola"; '
            '} '
            'fn main() { }'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'obtener' in error.descripcion
            and 'i32' in error.descripcion
            and 'String' in error.descripcion
            for error in errors.get_all()
        )


    def test_return_vacio_en_funcion_tipificada(self):
        _, _, errors = _semantic(
            'fn obtener() -> i32 { '
            'return; '
            '} '
            'fn main() { }'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'obtener' in error.descripcion
            and 'i32' in error.descripcion
            for error in errors.get_all()
        )


    def test_return_vacio_en_funcion_sin_tipo(self):
        _, _, errors = _semantic(
            'fn saludar() { '
            'return; '
            '} '
            'fn main() { }'
        )

        assert not errors.has_errors()


    def test_return_valor_en_funcion_sin_tipo(self):
        _, _, errors = _semantic(
            'fn saludar() { '
            'return 10; '
            '} '
            'fn main() { }'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'saludar' in error.descripcion
            and 'no debe retornar' in error.descripcion
            for error in errors.get_all()
        )


    def test_return_dentro_de_if_conserva_contexto(self):
        _, _, errors = _semantic(
            'fn obtener() -> i32 { '
            'if true { '
            'return 10; '
            '} '
            '} '
            'fn main() { }'
        )

        assert not errors.has_errors()


class TestArrays:

    def test_inferencia_array_i32(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let numeros = [10, 20, 30]; '
            '}'
        )

        assert not errors.has_errors()

        numeros = analyzer.function_envs[
            'main'
        ].lookup('numeros')

        assert numeros.tipo == (
            'array',
            'i32',
            3
        )


    def test_array_tipo_explicito_valido(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let numeros: [i32; 3] = [10, 20, 30]; '
            '}'
        )

        assert not errors.has_errors()

        numeros = analyzer.function_envs[
            'main'
        ].lookup('numeros')

        assert numeros.tipo == (
            'array',
            'i32',
            3
        )


    def test_array_elementos_diferentes_error(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let valores = [10, "hola", 20]; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'mismo tipo' in error.descripcion
            for error in errors.get_all()
        )


    def test_array_longitud_incompatible(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let numeros: [i32; 2] = [10, 20, 30]; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and '[i32; 2]' in error.descripcion
            and '[i32; 3]' in error.descripcion
            for error in errors.get_all()
        )


    def test_array_repeat(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let numeros = [0; 5]; '
            '}'
        )

        assert not errors.has_errors()

        numeros = analyzer.function_envs[
            'main'
        ].lookup('numeros')

        assert numeros.tipo == (
            'array',
            'i32',
            5
        )


    def test_array_vacio_sin_tipo_error(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let numeros = []; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'inferir' in error.descripcion
            for error in errors.get_all()
        )


    def test_array_vacio_con_tipo_valido(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let numeros: [i32; 0] = []; '
            '}'
        )

        assert not errors.has_errors()


    def test_acceso_array_devuelve_tipo_elemento(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let numeros = [10, 20, 30]; '
            'let x = numeros[1]; '
            '}'
        )

        assert not errors.has_errors()

        x = analyzer.function_envs[
            'main'
        ].lookup('x')

        assert x.tipo == 'i32'


    def test_indice_debe_ser_i32(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let numeros = [10, 20, 30]; '
            'let x = numeros[1.5]; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'índice' in error.descripcion
            and 'i32' in error.descripcion
            for error in errors.get_all()
        )


    def test_indice_fuera_de_limites(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let numeros = [10, 20, 30]; '
            'let x = numeros[5]; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'límites' in error.descripcion
            for error in errors.get_all()
        )


    def test_indice_negativo_fuera_de_limites(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let numeros = [10, 20, 30]; '
            'let x = numeros[-1]; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'límites' in error.descripcion
            for error in errors.get_all()
        )


class TestSlices:

    def test_slice_valido(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let numeros = [10, 20, 30, 40, 50]; '
            'let parte = &numeros[1..4]; '
            '}'
        )

        assert not errors.has_errors()

        parte = analyzer.function_envs[
            'main'
        ].lookup('parte')

        assert parte.tipo == (
            'slice',
            'i32'
        )


    def test_slice_fuera_de_limites(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let numeros = [10, 20, 30]; '
            'let parte = &numeros[1..5]; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'límites' in error.descripcion
            for error in errors.get_all()
        )


    def test_slice_inicio_mayor_fin(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let numeros = [10, 20, 30]; '
            'let parte = &numeros[2..1]; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'límites' in error.descripcion
            for error in errors.get_all()
        )


class TestArrayAssignments:

    def test_asignacion_elemento_array_mutable(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut numeros = [10, 20, 30]; '
            'numeros[1] = 50; '
            '}'
        )

        assert not errors.has_errors()


    def test_asignacion_elemento_array_inmutable(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let numeros = [10, 20, 30]; '
            'numeros[1] = 50; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'inmutable' in error.descripcion
            for error in errors.get_all()
        )


    def test_asignacion_elemento_tipo_incorrecto(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut numeros = [10, 20, 30]; '
            'numeros[1] = "hola"; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'i32' in error.descripcion
            and 'String' in error.descripcion
            for error in errors.get_all()
        )


    def test_compuesta_elemento_array(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut numeros = [10, 20, 30]; '
            'numeros[1] += 5; '
            '}'
        )

        assert not errors.has_errors()


class TestStructs:

    def test_inferencia_struct(self):
        _, analyzer, errors = _semantic(
            'struct Point { '
            'x: i32, '
            'y: i32, '
            '} '
            'fn main() { '
            'let p = Point { x: 10, y: 20 }; '
            '}'
        )

        assert not errors.has_errors()

        p = analyzer.function_envs[
            'main'
        ].lookup('p')

        assert p.tipo == 'Point'


    def test_struct_no_declarado(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let p = Point { x: 10 }; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'Point' in error.descripcion
            and 'no ha sido declarado' in error.descripcion
            for error in errors.get_all()
        )


    def test_struct_campo_faltante(self):
        _, _, errors = _semantic(
            'struct Point { x: i32, y: i32 } '
            'fn main() { '
            'let p = Point { x: 10 }; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'y' in error.descripcion
            and 'Falta' in error.descripcion
            for error in errors.get_all()
        )


    def test_struct_campo_inexistente(self):
        _, _, errors = _semantic(
            'struct Point { x: i32 } '
            'fn main() { '
            'let p = Point { x: 10, z: 20 }; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'z' in error.descripcion
            for error in errors.get_all()
        )


    def test_struct_tipo_campo_incorrecto(self):
        _, _, errors = _semantic(
            'struct Point { x: i32 } '
            'fn main() { '
            'let p = Point { x: "hola" }; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'x' in error.descripcion
            and 'i32' in error.descripcion
            and 'String' in error.descripcion
            for error in errors.get_all()
        )


    def test_struct_campo_repetido_en_init(self):
        _, _, errors = _semantic(
            'struct Point { x: i32 } '
            'fn main() { '
            'let p = Point { x: 1, x: 2 }; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'x' in error.descripcion
            and 'más de una vez' in error.descripcion
            for error in errors.get_all()
        )


    def test_acceso_campo_devuelve_tipo(self):
        _, analyzer, errors = _semantic(
            'struct Point { x: i32, y: f64 } '
            'fn main() { '
            'let p = Point { x: 10, y: 3.14 }; '
            'let valor = p.y; '
            '}'
        )

        assert not errors.has_errors()

        valor = analyzer.function_envs[
            'main'
        ].lookup('valor')

        assert valor.tipo == 'f64'


    def test_struct_anidado(self):
        _, analyzer, errors = _semantic(
            'struct Point { x: i32, y: i32 } '
            'struct Rectangle { position: Point } '
            'fn main() { '
            'let r = Rectangle { '
            'position: Point { x: 10, y: 20 } '
            '}; '
            'let valor = r.position.x; '
            '}'
        )

        assert not errors.has_errors()

        valor = analyzer.function_envs[
            'main'
        ].lookup('valor')

        assert valor.tipo == 'i32'


    def test_asignacion_campo_mutable(self):
        _, _, errors = _semantic(
            'struct Point { x: i32 } '
            'fn main() { '
            'let mut p = Point { x: 10 }; '
            'p.x = 20; '
            '}'
        )

        assert not errors.has_errors()


    def test_asignacion_campo_inmutable(self):
        _, _, errors = _semantic(
            'struct Point { x: i32 } '
            'fn main() { '
            'let p = Point { x: 10 }; '
            'p.x = 20; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'inmutable' in error.descripcion
            for error in errors.get_all()
        )


    def test_asignacion_campo_tipo_incorrecto(self):
        _, _, errors = _semantic(
            'struct Point { x: i32 } '
            'fn main() { '
            'let mut p = Point { x: 10 }; '
            'p.x = "hola"; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'i32' in error.descripcion
            and 'String' in error.descripcion
            for error in errors.get_all()
        )


    def test_campo_duplicado_en_struct(self):
        _, _, errors = _semantic(
            'struct Point { '
            'x: i32, '
            'x: f64, '
            '} '
            'fn main() { }'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'x' in error.descripcion
            and 'más de una vez' in error.descripcion
            for error in errors.get_all()
        )


    def test_tipo_struct_desconocido_en_campo(self):
        _, _, errors = _semantic(
            'struct Persona { '
            'direccion: NoExiste, '
            '} '
            'fn main() { }'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'NoExiste' in error.descripcion
            for error in errors.get_all()
        )


class TestBuiltins:

    def test_typeof_retorna_string(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let x = 10; '
            'let tipo = typeof(x); '
            '}'
        )

        assert not errors.has_errors()

        tipo = analyzer.function_envs[
            'main'
        ].lookup('tipo')

        assert tipo.tipo == 'String'


    def test_typeof_aridad_incorrecta(self):
        _, _, errors = _semantic(
            'fn main() { '
            'typeof(); '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'typeof' in error.descripcion
            for error in errors.get_all()
        )


    def test_random_i32(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let x = random(1, 10); '
            '}'
        )

        assert not errors.has_errors()

        x = analyzer.function_envs[
            'main'
        ].lookup('x')

        assert x.tipo == 'i32'


    def test_random_tipo_invalido(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x = random("a", 10); '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'random' in error.descripcion
            and 'numéricos' in error.descripcion
            for error in errors.get_all()
        )


    def test_string_len(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let texto = String::from("Hola"); '
            'let longitud = texto.len(); '
            '}'
        )

        assert not errors.has_errors()

        longitud = analyzer.function_envs[
            'main'
        ].lookup('longitud')

        assert longitud.tipo == 'i32'


    def test_string_contains(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let texto = String::from("Hola"); '
            'let existe = texto.contains("ola"); '
            '}'
        )

        assert not errors.has_errors()

        existe = analyzer.function_envs[
            'main'
        ].lookup('existe')

        assert existe.tipo == 'bool'


    def test_string_replace(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let texto = String::from("Hola Mundo"); '
            'let nuevo = texto.replace("Mundo", "Rust"); '
            '}'
        )

        assert not errors.has_errors()

        nuevo = analyzer.function_envs[
            'main'
        ].lookup('nuevo')

        assert nuevo.tipo == 'String'


    def test_string_split(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let texto = String::from("Hola Mundo"); '
            'let partes = texto.split(" "); '
            '}'
        )

        assert not errors.has_errors()

        partes = analyzer.function_envs[
            'main'
        ].lookup('partes')

        assert partes.tipo == (
            'array',
            'String',
            None
        )


    def test_uppercase_lowercase(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let texto = String::from("Hola"); '
            'let a = texto.to_uppercase(); '
            'let b = texto.to_lowercase(); '
            '}'
        )

        assert not errors.has_errors()

        env = analyzer.function_envs[
            'main'
        ]

        assert env.lookup('a').tipo == 'String'
        assert env.lookup('b').tipo == 'String'


    def test_array_len(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let numeros = [1, 2, 3]; '
            'let longitud = numeros.len(); '
            '}'
        )

        assert not errors.has_errors()

        longitud = analyzer.function_envs[
            'main'
        ].lookup('longitud')

        assert longitud.tipo == 'i32'


    def test_array_contains(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let numeros = [1, 2, 3]; '
            'let existe = numeros.contains(2); '
            '}'
        )

        assert not errors.has_errors()

        existe = analyzer.function_envs[
            'main'
        ].lookup('existe')

        assert existe.tipo == 'bool'


    def test_reverse_array_mutable(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut numeros = [1, 2, 3]; '
            'numeros.reverse(); '
            '}'
        )

        assert not errors.has_errors()


    def test_reverse_array_inmutable(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let numeros = [1, 2, 3]; '
            'numeros.reverse(); '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'inmutable' in error.descripcion
            for error in errors.get_all()
        )


    def test_metodo_no_existe(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let texto = String::from("Hola"); '
            'texto.no_existe(); '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'no_existe' in error.descripcion
            for error in errors.get_all()
        )


