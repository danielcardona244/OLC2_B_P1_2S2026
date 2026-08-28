from pathlib import Path

from interpreter.runtime.runner import run_source


ROOT = Path(__file__).resolve().parents[2]
AUXILIAR = ROOT / 'tests' / 'fixtures' / 'prueba_auxiliar.ox'


def _run(code):
    result = run_source(code)

    assert not result['errors'].has_errors(), (
        '\n'.join(
            str(error)
            for error in result['errors'].get_all()
        )
    )

    return result['output']


class TestRuntimeBase:

    def test_main_es_punto_de_entrada(self):
        output = _run(
            'fn otra() { println!("NO"); } '
            'fn main() { println!("SI"); }'
        )

        assert output == 'SI'


    def test_variables_y_println(self):
        output = _run(
            'fn main() { '
            'let x = 10; '
            'let y = 20; '
            'println!("{} {}", x, y); '
            '}'
        )

        assert output == '10 20'


    def test_defaults_primitivos(self):
        output = _run(
            'fn main() { '
            'let a: i32; '
            'let b: f64; '
            'let c: bool; '
            'let d: String; '
            'println!("{}", a); '
            'println!("{}", b); '
            'println!("{}", c); '
            'println!("{}", d); '
            '}'
        )

        assert output.splitlines()[:3] == [
            '0',
            '0.0',
            'false',
        ]


    def test_shadowing(self):
        output = _run(
            'fn main() { '
            'let x = 10; '
            'println!("{}", x); '
            'let x = 20; '
            'println!("{}", x); '
            '}'
        )

        assert output == '10\n20'


    def test_asignaciones_compuestas(self):
        output = _run(
            'fn main() { '
            'let mut x = 10; '
            'x += 5; '
            'x -= 3; '
            'x *= 2; '
            'x /= 4; '
            'println!("{}", x); '
            '}'
        )

        assert output == '6'


class TestRuntimeExpresiones:

    def test_promocion_i32_f64(self):
        output = _run(
            'fn main() { '
            'println!("{}", 10 + 2.5); '
            '}'
        )

        assert output == '12.5'


    def test_division_i32_conserva_i32(self):
        output = _run(
            'fn main() { '
            'println!("{}", 20 / 4); '
            '}'
        )

        assert output == '5'


    def test_string_concat_y_repeticion(self):
        output = _run(
            'fn main() { '
            'let a = String::from("Ha"); '
            'println!("{}", a * 3); '
            'println!("{}", a + String::from("!")); '
            '}'
        )

        assert output == 'HaHaHa\nHa!'


    def test_booleanos_se_imprimen_lowercase(self):
        output = _run(
            'fn main() { '
            'println!("{}", true); '
            'println!("{}", false); '
            '}'
        )

        assert output == 'true\nfalse'


    def test_corto_circuito_and(self):
        output = _run(
            'fn ruido() -> bool { '
            'println!("NO DEBE SALIR"); '
            'return true; '
            '} '
            'fn main() { '
            'let x = false && ruido(); '
            'println!("{}", x); '
            '}'
        )

        assert output == 'false'


    def test_corto_circuito_or(self):
        output = _run(
            'fn ruido() -> bool { '
            'println!("NO DEBE SALIR"); '
            'return false; '
            '} '
            'fn main() { '
            'let x = true || ruido(); '
            'println!("{}", x); '
            '}'
        )

        assert output == 'true'


class TestRuntimeFuncionesYControl:

    def test_funcion_retorna_valor(self):
        output = _run(
            'fn sumar(a: i32, b: i32) -> i32 { '
            'return a + b; '
            '} '
            'fn main() { '
            'println!("{}", sumar(10, 5)); '
            '}'
        )

        assert output == '15'


    def test_if_else(self):
        output = _run(
            'fn main() { '
            'let x = 10; '
            'if x > 5 { '
            'println!("A"); '
            '} else { '
            'println!("B"); '
            '} '
            '}'
        )

        assert output == 'A'


    def test_while_continue(self):
        output = _run(
            'fn main() { '
            'let mut i = 0; '
            'while i < 4 { '
            'i += 1; '
            'if i == 2 { continue; } '
            'println!("{}", i); '
            '} '
            '}'
        )

        assert output == '1\n3\n4'


    def test_loop_break(self):
        output = _run(
            'fn main() { '
            'let mut i = 0; '
            'loop { '
            'if i == 3 { break; } '
            'println!("{}", i); '
            'i += 1; '
            '} '
            '}'
        )

        assert output == '0\n1\n2'


    def test_break_etiquetado(self):
        output = _run(
            "fn main() {\n"
            "    'outer: loop {\n"
            "        loop {\n"
            "            break 'outer;\n"
            "        }\n"
            "    }\n"
            '    println!("FIN");\n'
            "}"
        )

        assert output == 'FIN'


    def test_match(self):
        output = _run(
            'fn main() { '
            'let x = 2; '
            'match x { '
            '1 => println!("UNO"), '
            '2 => println!("DOS"), '
            '_ => println!("OTRO"), '
            '} '
            '}'
        )

        assert output == 'DOS'


class TestRuntimeDatosYBuiltins:

    def test_arrays_acceso_slice_len(self):
        output = _run(
            'fn main() { '
            'let nums = [10, 20, 30, 40]; '
            'println!("{}", nums[1]); '
            'println!("{}", nums.len()); '
            'let parte = &nums[1..3]; '
            'println!("{:?}", parte); '
            '}'
        )

        assert output == '20\n4\n[20, 30]'


    def test_array_reverse(self):
        output = _run(
            'fn main() { '
            'let mut nums = [10, 20, 30]; '
            'nums.reverse(); '
            'println!("{:?}", nums); '
            '}'
        )

        assert output == '[30, 20, 10]'


    def test_string_methods(self):
        output = _run(
            'fn main() { '
            'let s = String::from("Hola Mundo"); '
            'println!("{}", s.len()); '
            'println!("{}", s.contains("Mundo")); '
            'println!("{}", s.replace("Mundo", "Rust")); '
            'println!("{}", s.to_uppercase()); '
            'println!("{}", s.to_lowercase()); '
            'println!("{:?}", s.split(" ")); '
            '}'
        )

        assert output == (
            '10\n'
            'true\n'
            'Hola Rust\n'
            'HOLA MUNDO\n'
            'hola mundo\n'
            '["Hola", "Mundo"]'
        )


    def test_struct_anidado(self):
        output = _run(
            'struct Point { x: i32, y: i32 } '
            'struct Rectangle { position: Point } '
            'fn main() { '
            'let r = Rectangle { '
            'position: Point { x: 5, y: 15 } '
            '}; '
            'println!("{}", r.position.x); '
            'println!("{}", r.position.y); '
            '}'
        )

        assert output == '5\n15'


    def test_typeof(self):
        output = _run(
            'fn main() { '
            'let x: i32 = 10; '
            'println!("{}", typeof(x)); '
            '}'
        )

        assert output == 'i32'


    def test_random_i32_en_rango(self):
        output = _run(
            'fn main() { '
            'println!("{}", random(1, 3)); '
            '}'
        )

        value = int(output)
        assert 1 <= value <= 3


def test_archivo_auxiliar_runtime_smoke():
    assert AUXILIAR.exists()

    result = run_source(
        AUXILIAR.read_text(
            encoding='utf-8'
        )
    )

    assert not result['errors'].has_errors(), (
        '\n'.join(
            str(error)
            for error in result['errors'].get_all()
        )
    )

    lines = result['output'].splitlines()

    assert lines[0] == '=== INICIO DE PRUEBAS ==='
    assert lines[-1] == '=== FIN DE PRUEBAS ==='

    # Salidas distintivas del archivo entregado por el auxiliar.
    assert 'Valor retornado: 10' in lines
    assert 'Fuera de los loops' in lines
    assert '[20, 30, 40]' in lines
    assert 'Hola, Ana' in lines
    assert 'Resultado: 15' in lines
    assert '["Hola", "Mundo"]' in lines
    assert '[30, 20, 10]' in lines
