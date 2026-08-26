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