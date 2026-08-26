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


    def test_tabla_contiene_funciones_y_structs(self):
        _, analyzer, errors = _semantic(
            'struct Point { x: i32 } '
            'fn sumar(a: i32, b: i32) -> i32 { '
            'return a + b; '
            '} '
            'fn main() { }'
        )

        assert not errors.has_errors()

        symbols = analyzer.symbol_table.get_all()

        assert len(symbols) == 3

        categorias = [
            symbol.categoria
            for symbol in symbols
        ]

        assert categorias == [
            'struct',
            'funcion',
            'funcion'
        ]


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