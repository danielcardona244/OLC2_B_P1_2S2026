from interpreter.errors import ErrorList
from interpreter.parser.parser import parse
from interpreter.semantic.analyzer import SemanticAnalyzer


def _semantic(code):
    errors = ErrorList()
    ast = parse(code, errors)

    analyzer = SemanticAnalyzer(
        errors=errors,
        source_code=code
    )
    analyzer.analyze(ast)

    return ast, analyzer, errors


class TestLoopTransfer:

    def test_break_en_loop_valido(self):
        _, _, errors = _semantic(
            'fn main() { loop { break; } }'
        )

        assert not errors.has_errors()

    def test_continue_en_loop_valido(self):
        _, _, errors = _semantic(
            'fn main() { loop { continue; } }'
        )

        assert not errors.has_errors()

    def test_break_fuera_de_ciclo_error(self):
        _, _, errors = _semantic(
            'fn main() { break; }'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'break' in error.descripcion
            and 'ciclo' in error.descripcion
            for error in errors.get_all()
        )

    def test_continue_fuera_de_ciclo_error(self):
        _, _, errors = _semantic(
            'fn main() { continue; }'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'continue' in error.descripcion
            and 'ciclo' in error.descripcion
            for error in errors.get_all()
        )

    def test_break_con_label_externo_valido(self):
        _, _, errors = _semantic(
            "fn main() {\n"
            "    'outer: loop {\n"
            "        loop {\n"
            "            break 'outer;\n"
            "        }\n"
            "    }\n"
            "}"
        )

        assert not errors.has_errors()

    def test_break_label_inexistente_error(self):
        _, _, errors = _semantic(
            "fn main() {\n"
            "    'outer: loop {\n"
            "        break 'otro;\n"
            "    }\n"
            "}"
        )

        assert any(
            error.tipo == 'Semántico'
            and 'otro' in error.descripcion
            for error in errors.get_all()
        )

    def test_continue_label_inexistente_error(self):
        _, _, errors = _semantic(
            "fn main() {\n"
            "    'outer: loop {\n"
            "        continue 'otro;\n"
            "    }\n"
            "}"
        )

        assert any(
            error.tipo == 'Semántico'
            and 'otro' in error.descripcion
            for error in errors.get_all()
        )

    def test_break_dentro_de_while_valido(self):
        _, _, errors = _semantic(
            'fn main() { '
            'while true { break; } '
            '}'
        )

        assert not errors.has_errors()


class TestMatchSemantic:

    def test_match_tipos_compatibles(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x = 10; '
            'match x { '
            '10 => println!("diez"), '
            '_ => println!("otro"), '
            '} '
            '}'
        )

        assert not errors.has_errors()

    def test_match_patron_tipo_incompatible(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x = 10; '
            'match x { '
            '"diez" => println!("diez"), '
            '_ => println!("otro"), '
            '} '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'patrón' in error.descripcion
            and 'String' in error.descripcion
            and 'i32' in error.descripcion
            for error in errors.get_all()
        )

    def test_match_patron_identificador_valido(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x = 10; '
            'let limite = 10; '
            'match x { '
            'limite => println!("limite"), '
            '_ => println!("otro"), '
            '} '
            '}'
        )

        assert not errors.has_errors()

    def test_match_bloque_crea_scope(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x = 1; '
            'match x { '
            '1 => { let interno = 10; println!(interno); }, '
            '_ => { println!("otro"); }, '
            '} '
            'println!(interno); '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'interno' in error.descripcion
            and 'no ha sido declarada' in error.descripcion
            for error in errors.get_all()
        )


class TestInitializationSemantic:

    def test_tipos_primitivos_con_default_se_pueden_usar(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let a: i32; '
            'let b: f64; '
            'let c: bool; '
            'let d: String; '
            'println!(a, b, c, d); '
            '}'
        )

        assert not errors.has_errors()

        env = analyzer.function_envs['main']
        assert env.lookup('a').valor == 0
        assert env.lookup('b').valor == 0.0
        assert env.lookup('c').valor is False
        assert env.lookup('d').valor == ''

    def test_asignacion_a_inmutable_con_default_es_error(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x: i32; '
            'x = 10; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'x' in error.descripcion
            and 'inmutable' in error.descripcion
            for error in errors.get_all()
        )

    def test_mutable_con_default_puede_asignarse(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut x: i32; '
            'x = 10; '
            'println!(x); '
            '}'
        )

        assert not errors.has_errors()

    def test_inferencia_diferida_sin_tipo(self):
        _, analyzer, errors = _semantic(
            'fn main() { '
            'let x; '
            'x = 10; '
            'let y = x + 1; '
            '}'
        )

        assert not errors.has_errors()
        assert analyzer.function_envs['main'].lookup('x').tipo == 'i32'
        assert analyzer.function_envs['main'].lookup('y').tipo == 'i32'

    def test_compuesta_sobre_mutable_con_default_es_valida(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let mut x: i32; '
            'x += 1; '
            '}'
        )

        assert not errors.has_errors()

    def test_parametro_se_considera_inicializado(self):
        _, _, errors = _semantic(
            'fn identidad(x: i32) -> i32 { '
            'return x; '
            '} '
            'fn main() { '
            'let y = identidad(10); '
            '}'
        )

        assert not errors.has_errors()


class TestDeclaredTypesFinal:

    def test_tipo_local_no_declarado_error(self):
        _, _, errors = _semantic(
            'fn main() { '
            'let x: NoExiste; '
            '}'
        )

        assert any(
            error.tipo == 'Semántico'
            and 'NoExiste' in error.descripcion
            and 'no ha sido declarado' in error.descripcion
            for error in errors.get_all()
        )

    def test_tipos_invalidos_en_firma_funcion(self):
        _, _, errors = _semantic(
            'fn prueba(x: NoExiste) -> OtroTipo { '
            'return x; '
            '} '
            'fn main() { }'
        )

        descriptions = [
            error.descripcion
            for error in errors.get_all()
            if error.tipo == 'Semántico'
        ]

        assert any('NoExiste' in desc for desc in descriptions)
        assert any('OtroTipo' in desc for desc in descriptions)
