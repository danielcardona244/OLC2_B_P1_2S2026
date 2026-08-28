// ============================================================================
// ARCHIVO DE PRUEBA PARA OXIGENSCRIPT
// Valida cada numeral de la definición del lenguaje (secciones 3.2 - 3.5)
// ============================================================================

// ============================================================================
// SECCIÓN 3.2.1: IDENTIFICADORES
// Case sensitive, debe comenzar con letra o _, seguido de letras, dígitos o _
// ============================================================================
fn test_identificadores() {
    let edad = 20;
    let Edad = 25;
    let EDAD = 30;
    let _privada = 100;
    let variable123 = 456;
    
    println!("{}", edad);    // 20
    println!("{}", Edad);    // 25
    println!("{}", EDAD);    // 30
    println!("{}", _privada); // 100
    println!("{}", variable123); // 456
}

// ============================================================================
// SECCIÓN 3.2.2: COMENTARIOS
// Comentario de línea (//) y de bloque (/* */)
// ============================================================================
fn test_comentarios() {
    // Este es un comentario de línea
    let x: i32 = 10;
    let y: i32 = 20; // Otro comentario en línea
    
    /*
       Este es un comentario
       de bloque multilínea
    */
    let resultado = x + y;
    
    println!("{}", resultado); // 30
}

// ============================================================================
// SECCIÓN 3.2.3: TIPOS ESTÁTICOS
// Tipos: i32, f64, bool, char, String, [T; N]
// Declaración explícita e inferencia de tipos
// ============================================================================
fn test_tipos() {
    // Tipos explícitos
    let entero: i32 = 10;
    let decimal: f64 = 3.14;
    let booleano: bool = true;
    let caracter: char = 'A';
    let texto = String::from("Hola");
    
    // Valores por defecto (declaración sin inicialización)
    let contador: i32;
    let promedio: f64;
    let activo: bool;
    let mensaje: String;
    
    println!("{}", entero);      // 10
    println!("{}", decimal);     // 3.14
    println!("{}", booleano);    // true
    println!("{}", caracter);    // A
    println!("{}", texto);       // Hola
    
    println!("{}", contador);    // 0
    println!("{}", promedio);    // 0.0
    println!("{}", activo);      // false
    println!("{}", mensaje);     // "" (cadena vacía)
}

// ============================================================================
// SECCIÓN 3.3.1: BLOQUES DE SENTENCIAS
// Bloques con {} definen scope
// ============================================================================
fn test_bloques() {
    let exterior: i32 = 10;
    
    {
        let interior: i32 = 20;
        println!("{}", interior); // 20
        println!("{}", exterior); // 10 (accesible desde bloque interno)
    }
    
    // println!("{}", interior); // ERROR: interior no existe en este scope
    println!("{}", exterior); // 10
}

// ============================================================================
// SECCIÓN 3.3.2: VARIABLES
// Declaración con let, con/sin tipo, con/sin valor inicial
// ============================================================================
fn test_variables() {
    // Con tipo y valor explícitos
    let entero: i32 = 10;
    
    // Con inferencia de tipo
    let inferido = 20;
    
    // Sin valor inicial (usa valor por defecto)
    let sin_valor: i32;
    
    println!("{}", entero);     // 10
    println!("{}", inferido);   // 20
    println!("{}", sin_valor);  // 0
    
    // Shadowing (sombreado)
    let var_sombreada: i32 = 10;
    println!("{}", var_sombreada); // 10
    
    let var_sombreada: f64 = 3.14;
    println!("{}", var_sombreada); // 3.14
}

// ============================================================================
// SECCIÓN 3.3.3: INMUTABILIDAD Y MUTABILIDAD
// Variables inmutables por defecto, mut con la palabra mut
// ============================================================================
fn test_mutabilidad() {
    // Variable inmutable
    let inmutable = 20;
    println!("{}", inmutable); // 20
    // inmutable = 21; // ERROR: no se puede modificar variable inmutable
    
    // Variable mutable
    let mut contador = 0;
    println!("{}", contador); // 0
    
    contador = 10;
    println!("{}", contador); // 10
}

// ============================================================================
// SECCIÓN 3.3.4: OPERADORES DE ASIGNACIÓN
// =, +=, -=, *=, /=, %=
// ============================================================================
fn test_asignacion() {
    let mut x: i32 = 10;
    
    x = 5;
    println!("{}", x); // 5
    
    x += 3;
    println!("{}", x); // 8
    
    x -= 2;
    println!("{}", x); // 6
    
    x *= 4;
    println!("{}", x); // 24
    
    x /= 6;
    println!("{}", x); // 4
    
    let mut z: i32 = 17;
    z %= 5;
    println!("{}", z); // 2
}

// ============================================================================
// SECCIÓN 3.3.5: OPERADORES ARITMÉTICOS
// +, -, *, /, %, negación unaria (-)
// Tabla de promoción de tipos
// ============================================================================
fn test_aritmetica() {
    let a: i32 = 10;
    let b: f64 = 2.5;
    
    // Suma con promoción de tipos
    let suma1 = a + b;
    println!("{}", suma1); // 12.5
    
    // Multiplicación
    let producto = a * 5;
    println!("{}", producto); // 50
    
    // División
    let division = 20 / 4;
    println!("{}", division); // 5
    
    // Módulo
    let modulo = 17 % 5;
    println!("{}", modulo); // 2
    
    // Negación unaria
    let negativo = -a;
    println!("{}", negativo); // -10
    
    // String * i32 (repetición)
    let texto = String::from("Hola");
    let repetido = texto * 3;
    println!("{}", repetido); // "HolaHolaHola"
    
    // String + String (concatenación)
    let saludo = String::from("Hola ");
    let mundo = String::from("Mundo");
    let completo = saludo + mundo;
    println!("{}", completo); // "Hola Mundo"
}

// ============================================================================
// SECCIÓN 3.3.6: OPERADORES RELACIONALES
// ==, !=, >, >=, <, <=
// ============================================================================
fn test_relacionales() {
    let x: i32 = 10;
    let y: i32 = 20;
    
    // Igualdad
    let igual = x == y;
    println!("{}", igual); // false
    
    let igual2 = x == 10;
    println!("{}", igual2); // true
    
    // Desigualdad
    let diferente = x != y;
    println!("{}", diferente); // true
    
    // Mayor/Menor
    let mayor = y > x;
    println!("{}", mayor); // true
    
    let menor = x < y;
    println!("{}", menor); // true
    
    // Mayor/Menor o igual
    let mayor_igual = y >= 20;
    println!("{}", mayor_igual); // true
    
    let menor_igual = x <= 10;
    println!("{}", menor_igual); // true
}

// ============================================================================
// SECCIÓN 3.3.7: OPERADORES LÓGICOS
// !, &&, || con corto circuito
// ============================================================================
fn test_logicos() {
    let a: bool = true;
    let b: bool = false;
    
    // Negación
    let negacion = !a;
    println!("{}", negacion); // false
    
    // AND
    let and_result = a && b;
    println!("{}", and_result); // false
    
    // OR
    let or_result = a || b;
    println!("{}", or_result); // true
    
    // Corto circuito: si el primer operando es false, no evalúa el segundo
    let flag: bool = false;
    // flag && funcion_costosa() no ejecuta funcion_costosa()
}

// ============================================================================
// SECCIÓN 3.3.8: CONTROL DE FLUJO
// if, while, loop, match
// ============================================================================
fn test_control_flujo() {
    // IF
    let x: i32 = 10;
    if x > 5 {
        println!("Mayor que 5"); // Mayor que 5
    }
    
    // IF-ELSE
    let flag: bool = false;
    if flag {
        println!("Verdadero");
    } else if flag == false {
        println!("Falso"); // Falso
    } else {
        println!("Otro caso");
    }
    
    // WHILE
    let mut contador: i32 = 0;
    while contador < 3 {
        println!("{}", contador); // 0, 1, 2
        contador = contador + 1;
    }
    
    // LOOP
    let mut i: i32 = 0;
    loop {
        if i >= 3 {
            break;
        }
        println!("Loop {}", i); // Loop 0, Loop 1, Loop 2
        i = i + 1;
    }
    
    // LOOP con etiquetas
    let mut outer_count: i32 = 0;
    'outer: loop {
        if outer_count >= 2 {
            break;
        }
        
        let mut inner_count: i32 = 0;
        'inner: loop {
            if inner_count >= 2 {
                break 'inner;
            }
            println!("({}, {})", outer_count, inner_count);
            inner_count = inner_count + 1;
        }
        
        outer_count = outer_count + 1;
    }
    
    // MATCH
    let numero: i32 = 2;
    match numero {
        1 => println!("UNO"),
        2 => println!("DOS"), // DOS
        _ => println!("OTRO"),
    }
}

// ============================================================================
// SECCIÓN 3.3.9: SENTENCIAS DE TRANSFERENCIA
// break, continue, return
// ============================================================================
fn test_transferencia() -> i32 {
    // RETURN
    let mut x: i32 = 5;
    if x > 3 {
        return x * 2; // Retorna 10
    }
    return 0;
}

fn test_continue() {
    // CONTINUE
    let mut i: i32 = 0;
    while i < 5 {
        i = i + 1;
        if i == 3 {
            continue; // Salta el 3
        }
        println!("{}", i); // 1, 2, 4, 5
    }
}

fn test_break_etiqueta() {
    // BREAK con etiqueta
    'outer: loop {
        'inner: loop {
            break 'outer; // Sale del loop outer
            println!("Esto no se ejecuta");
        }
    }
    println!("Fuera de los loops");
}

// ============================================================================
// SECCIÓN 3.3.10: ARREGLOS Y SLICES
// Arreglos de tamaño fijo [T; N], acceso por índice, slices
// ============================================================================
fn test_arreglos() {
    // Declaración explícita
    let numeros: [i32; 5] = [10, 20, 30, 40, 50];
    
    // Declaración por inferencia
    let edades = [18, 20, 22];
    
    // Acceso por índice
    println!("{}", numeros[0]); // 10
    println!("{}", numeros[2]); // 30
    
    // Longitud
    println!("{}", numeros.len()); // 5
    println!("{}", edades.len());  // 3
    
    // Recorrer con while
    let mut i = 0;
    while i < numeros.len() {
        println!("{}", numeros[i]);
        i = i + 1;
    }
    
    // Slice
    let parte = &numeros[1..4];
    println!("{:?}", parte); // [20, 30, 40]
}

// ============================================================================
// SECCIÓN 3.3.11: STRINGS
// String::from(), String::new(), métodos de String
// ============================================================================
fn test_strings() {
    // Creación
    let saludo = String::from("Hola Mundo");
    println!("{}", saludo); // Hola Mundo
    
    // Longitud
    println!("{}", saludo.len()); // 10
    
    // Métodos
    println!("{}", saludo.contains("Mundo")); // true
    println!("{}", saludo.replace("Mundo", "Rust")); // Hola Rust
    println!("{}", saludo.to_uppercase()); // HOLA MUNDO
    println!("{}", saludo.to_lowercase()); // hola mundo
    
    // Split
    let palabras = saludo.split(" ");
    println!("{:?}", palabras); // ["Hola", "Mundo"]
    
    // Secuencias de escape
    let mensaje = String::from("Hola\nMundo");
    println!("{}", mensaje); // Hola
                             // Mundo
    
    let comillas = String::from("Él dijo: \"Hola\"");
    println!("{}", comillas); // Él dijo: "Hola"
    
    // Raw strings
    let ruta = String::from(r"C:\Users\Diego");
    println!("{}", ruta); // C:\Users\Diego
}

// ============================================================================
// SECCIÓN 3.3.12: STRUCTS
// Definición e instanciación de structs
// ============================================================================
struct Point {
    x: i32,
    y: i32,
}

struct Rectangle {
    position: Point,
}

fn test_structs() {
    // Instanciación
    let punto = Point {
        x: 10,
        y: 20,
    };
    
    // Acceso a campos
    println!("{}", punto.x); // 10
    println!("{}", punto.y); // 20
    
    // Struct anidado
    let rectangulo = Rectangle {
        position: Point {
            x: 5,
            y: 15,
        },
    };
    
    println!("{}", rectangulo.position.x); // 5
    println!("{}", rectangulo.position.y); // 15
}

// ============================================================================
// SECCIÓN 3.3.13: FUNCIONES Y PARÁMETROS
// Declaración de funciones con/sin retorno
// ============================================================================
fn saludar(nombre: String) {
    println!("Hola, {}", nombre);
}

fn sumar(a: i32, b: i32) -> i32 {
    return a + b;
}

fn test_funciones() {
    saludar(String::from("Ana")); // Hola, Ana
    
    let resultado = sumar(10, 5);
    println!("Resultado: {}", resultado); // Resultado: 15
}

// ============================================================================
// SECCIÓN 3.3.14: FUNCIONES EMBEBIDAS
// println!, typeof, random, len, contains, replace, split, etc.
// ============================================================================
fn test_funciones_embebidas() {
    let texto = String::from("Hola Mundo");
    let mut numeros = [10, 20, 30];
    
    // println!
    println!("Hola Mundo");
    println!("{}", texto);
    println!("Texto: {}", texto);
    
    // typeof
    println!("{}", typeof(texto)); // String
    
    // len
    println!("{}", texto.len()); // 10
    
    // contains
    println!("{}", texto.contains("Mundo")); // true
    
    // replace
    println!("{}", texto.replace("Mundo", "Rust")); // Hola Rust
    
    // to_uppercase / to_lowercase
    println!("{}", texto.to_uppercase()); // HOLA MUNDO
    println!("{}", texto.to_lowercase()); // hola mundo
    
    // split
    println!("{:?}", texto.split(" ")); // ["Hola", "Mundo"]
    
    // reverse (arreglos)
    numeros.reverse();
    println!("{:?}", numeros); // [30, 20, 10]
    
    // random
    println!("{}", random(1, 10)); // Número aleatorio entre 1 y 10
}

// ============================================================================
// SECCIÓN 3.3.15: FUNCIÓN MAIN
// Punto de entrada del programa
// ============================================================================
fn main() {
    println!("=== INICIO DE PRUEBAS ===");
    
    // Ejecutar todas las pruebas
    test_identificadores();
    test_comentarios();
    test_tipos();
    test_bloques();
    test_variables();
    test_mutabilidad();
    test_asignacion();
    test_aritmetica();
    test_relacionales();
    test_logicos();
    test_control_flujo();
    
    let valor = test_transferencia();
    println!("Valor retornado: {}", valor); // 10
    
    test_continue();
    test_break_etiqueta();
    
    test_arreglos();
    test_strings();
    test_structs();
    test_funciones();
    test_funciones_embebidas();
    
    println!("=== FIN DE PRUEBAS ===");
}

// ============================================================================
// RESULTADO ESPERADO (consola):
// ============================================================================
// === INICIO DE PRUEBAS ===
// 20
// 25
// 30
// 100
// 456
// 30
// 10
// 3.14
// true
// A
// Hola
// 0
// 0.0
// false
// ""
// 20
// 10
// 10
// 10
// 20
// 10
// 20
// 10
// 3.14
// 20
// 0
// 10
// 5
// 8
// 6
// 24
// 4
// 2
// 12.5
// 50
// 5
// 2
// -10
// HolaHolaHola
// Hola Mundo
// false
// true
// true
// true
// true
// true
// false
// true
// false
// true
// true
// Mayor que 5
// Falso
// 0
// 1
// 2
// Loop 0
// Loop 1
// Loop 2
// (0, 0)
// (0, 1)
// (1, 0)
// (1, 1)
// DOS
// Valor retornado: 10
// 1
// 2
// 4
// 5
// Fuera de los loops
// 10
// 30
// 5
// 3
// 10
// 20
// 30
// 40
// 50
// 18
// 20
// 22
// [20, 30, 40]
// Hola Mundo
// 10
// Hola Mundo
// Hola
// Mundo
// Él dijo: "Hola"
// C:\Users\Diego
// 10
// 20
// 5
// 15
// Hola, Ana
// Resultado: 15
// Hola Mundo
// Hola Mundo
// Texto: Hola Mundo
// String
// 10
// true
// Hola Rust
// HOLA MUNDO
// hola mundo
// ["Hola", "Mundo"]
// [30, 20, 10]
// [número aleatorio]
// === FIN DE PRUEBAS ===
