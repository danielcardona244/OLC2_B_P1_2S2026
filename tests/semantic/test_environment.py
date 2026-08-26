from interpreter.errors import ErrorList
from interpreter.semantic.symbol import Symbol
from interpreter.semantic.symbol_table import SymbolTable
from interpreter.semantic.environment import Environment


class TestSymbol:

    def test_symbol_guarda_informacion(self):
        symbol = Symbol(
            nombre='contador',
            tipo='i32',
            categoria='variable',
            mutable=True,
            valor=10,
            linea=3,
            columna=5
        )

        assert symbol.nombre == 'contador'
        assert symbol.tipo == 'i32'
        assert symbol.categoria == 'variable'
        assert symbol.mutable is True
        assert symbol.valor == 10
        assert symbol.linea == 3
        assert symbol.columna == 5


class TestEnvironment:

    def test_declarar_y_buscar_variable(self):
        errors = ErrorList()
        env = Environment(
            nombre='main',
            errors=errors
        )

        symbol = Symbol(
            nombre='x',
            tipo='i32',
            categoria='variable',
            linea=1,
            columna=1
        )

        resultado = env.define(symbol)

        assert resultado is True
        assert env.lookup('x') is symbol
        assert not errors.has_errors()


    def test_redeclaracion_mismo_scope_genera_error(self):
        errors = ErrorList()

        env = Environment(
            nombre='main',
            errors=errors
        )

        primero = Symbol(
            nombre='x',
            tipo='i32',
            categoria='variable',
            linea=1,
            columna=5
        )

        segundo = Symbol(
            nombre='x',
            tipo='i32',
            categoria='variable',
            linea=2,
            columna=5
        )

        assert env.define(
            primero,
            'let x = 10;'
        ) is True

        assert env.define(
            segundo,
            'let x = 20;'
        ) is False

        assert errors.has_errors()

        error = errors.get_all()[0]

        assert error.tipo == 'Semántico'
        assert 'x' in error.descripcion
        assert error.linea == 2
        assert error.fragmento == 'let x = 20;'


    def test_scope_hijo_puede_ver_padre(self):
        global_env = Environment(
            nombre='global'
        )

        main_env = global_env.create_child('main')

        symbol = Symbol(
            nombre='x',
            tipo='i32',
            categoria='variable'
        )

        global_env.define(symbol)

        assert main_env.lookup('x') is symbol


    def test_shadowing_en_scope_hijo_es_valido(self):
        errors = ErrorList()

        global_env = Environment(
            nombre='global',
            errors=errors
        )

        main_env = global_env.create_child('main')

        x_global = Symbol(
            nombre='x',
            tipo='i32',
            categoria='variable'
        )

        x_main = Symbol(
            nombre='x',
            tipo='f64',
            categoria='variable'
        )

        assert global_env.define(x_global) is True
        assert main_env.define(x_main) is True

        assert main_env.lookup('x') is x_main
        assert global_env.lookup('x') is x_global

        assert not errors.has_errors()


    def test_padre_no_puede_ver_simbolos_del_hijo(self):
        global_env = Environment(
            nombre='global'
        )

        main_env = global_env.create_child('main')

        local = Symbol(
            nombre='local',
            tipo='i32',
            categoria='variable'
        )

        main_env.define(local)

        assert main_env.lookup('local') is local
        assert global_env.lookup('local') is None


    def test_lookup_local_no_busca_en_padre(self):
        global_env = Environment(
            nombre='global'
        )

        child = global_env.create_child('if_1')

        symbol = Symbol(
            nombre='x',
            tipo='i32',
            categoria='variable'
        )

        global_env.define(symbol)

        assert child.lookup('x') is symbol
        assert child.lookup_local('x') is None


    def test_identificadores_son_case_sensitive(self):
        errors = ErrorList()

        env = Environment(
            nombre='main',
            errors=errors
        )

        edad = Symbol(
            nombre='edad',
            tipo='i32',
            categoria='variable'
        )

        Edad = Symbol(
            nombre='Edad',
            tipo='i32',
            categoria='variable'
        )

        assert env.define(edad) is True
        assert env.define(Edad) is True

        assert env.lookup('edad') is edad
        assert env.lookup('Edad') is Edad

        assert not errors.has_errors()


class TestSymbolTable:

    def test_tabla_registra_simbolos(self):
        table = SymbolTable()

        env = Environment(
            nombre='global',
            symbol_table=table
        )

        a = Symbol(
            nombre='a',
            tipo='i32',
            categoria='variable'
        )

        b = Symbol(
            nombre='b',
            tipo='f64',
            categoria='variable'
        )

        env.define(a)
        env.define(b)

        symbols = table.get_all()

        assert len(symbols) == 2
        assert symbols[0] is a
        assert symbols[1] is b


    def test_tabla_conserva_shadowing(self):
        table = SymbolTable()

        global_env = Environment(
            nombre='global',
            symbol_table=table
        )

        child = global_env.create_child('main')

        x_global = Symbol(
            nombre='x',
            tipo='i32',
            categoria='variable'
        )

        x_local = Symbol(
            nombre='x',
            tipo='f64',
            categoria='variable'
        )

        global_env.define(x_global)
        child.define(x_local)

        symbols = table.get_all()

        assert len(symbols) == 2

        assert symbols[0].nombre == 'x'
        assert symbols[0].ambito == 'global'

        assert symbols[1].nombre == 'x'
        assert symbols[1].ambito == 'main'