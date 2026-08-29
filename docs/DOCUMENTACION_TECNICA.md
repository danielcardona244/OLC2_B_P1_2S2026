# Documentación técnica — OxigenScript

## 1. Objetivo

OxigenScript es un intérprete web para un lenguaje con sintaxis inspirada en Rust. El sistema recibe código fuente, realiza análisis léxico, sintáctico y semántico, construye un AST, ejecuta el programa y genera reportes.

La solución utiliza una arquitectura monolítica cliente/servidor: Django sirve la interfaz y expone una API REST en Python.

## 2. Tecnologías

| Componente | Tecnología |
|---|---|
| Lenguaje principal | Python |
| Lexer / Parser | PLY |
| Backend web | Django |
| Frontend | HTML, CSS y JavaScript |
| AST gráfico | Graphviz |
| Pruebas | pytest |
| Sistema operativo | Linux |

## 3. Arquitectura

```text
Código fuente
    ↓
Lexer
    ↓
Parser
    ↓
AST
    ↓
Análisis semántico
    ↓
Runtime / Intérprete
    ↓
Salida + Reportes
    ↓
API REST
    ↓
GUI Web
```

## 4. Gramática formal resumida

### Identificadores

```text
<identifier> ::= ( <letter> | "_" ) ( <letter> | <digit> | "_" )*
```

Los identificadores son case-sensitive.

### Tipos

```text
<type> ::= i32
         | f64
         | bool
         | char
         | String
         | [ <type> ; <integer> ]
         | <identifier>
```

### Variables

```text
<var_decl> ::= let <identifier> ;
             | let mut <identifier> ;
             | let <identifier> : <type> ;
             | let mut <identifier> : <type> ;
             | let <identifier> = <expression> ;
             | let mut <identifier> = <expression> ;
             | let <identifier> : <type> = <expression> ;
             | let mut <identifier> : <type> = <expression> ;
```

### Funciones

```text
<function_decl> ::= fn <identifier> "(" <param_list_opt> ")" <return_opt> <block>
<return_opt> ::= "->" <type> | ε
<param_list> ::= <param> | <param> "," <param_list>
<param> ::= <identifier> ":" <type>
```

El punto de entrada es una única función `main`.

### Bloques y control de flujo

```text
<block> ::= "{" <stmt_list> "}"
<if_stmt> ::= if <expression> <block> <else_opt>
<while_stmt> ::= while <expression> <block>
<loop_stmt> ::= <label_opt> loop <block>
<match_stmt> ::= match <expression> "{" <match_arms> "}"
```

También se implementan `break`, `continue` y `return`.

### Expresiones

Se soportan operadores aritméticos, relacionales, lógicos, unarios, llamadas a funciones y métodos, acceso a arreglos/slices y acceso a campos de structs.

## 5. Análisis léxico

El lexer reconoce palabras reservadas, identificadores, enteros, decimales, strings, chars, operadores, delimitadores, comentarios, etiquetas y `println!`.

Los errores registran tipo, descripción, línea, columna y fragmento.

## 6. Parser y AST

El parser utiliza PLY y construye clases de AST como:

`Program`, `FunctionDecl`, `StructDecl`, `VarDeclaration`, `Assignment`, `IfStmt`, `WhileStmt`, `LoopStmt`, `MatchStmt`, `Block`, `ReturnStmt`, `BreakStmt`, `ContinueStmt`, `Literal`, `Identifier`, `BinaryOp`, `UnaryOp`, `Comparison`, `LogicalOp`, `ArrayLiteral`, `ArrayAccess`, `SliceAccess`, `FunctionCall`, `MethodCall`, `StructInit` y `FieldAccess`.

## 7. Análisis semántico

Valida declaraciones, tipos, mutabilidad, scopes, parámetros, retornos, llamadas, arrays, slices, structs, condiciones booleanas, control de transferencia y existencia/unicidad de `main`.

Los entornos se organizan padre/hijo. Los símbolos locales son visibles en subámbitos, pero no hacia fuera.

### Tabla de símbolos

Columnas:

```text
No.
Identificador
Categoría
Tipo
Ámbito
Línea
Valor
```

El campo Ámbito indica dónde fue declarado el símbolo.

## 8. Runtime

El runtime recorre el AST y ejecuta el programa iniciando en `main`.

Implementa variables, entornos léxicos, control de flujo, funciones, arrays/slices, structs, operadores, `println!` y builtins.

`return`, `break` y `continue` utilizan señales internas para propagar cambios de flujo.

## 9. Funciones embebidas

```text
println!
typeof
random
len
contains
replace
split
to_uppercase
to_lowercase
reverse
```

## 10. Reportes

- Errores en HTML.
- Tabla de símbolos en HTML.
- AST en DOT y SVG con Graphviz.

Los archivos de `reports/` son generados automáticamente y no se versionan.

## 11. API REST

```text
GET  /api/health/
POST /api/execute/
GET  /api/reports/errors/
GET  /api/reports/symbols/
GET  /api/reports/ast/
```

Ejemplo de solicitud:

```json
{
  "code": "fn main() { println!(\"Hola\"); }"
}
```

## 12. GUI

Incluye Nuevo, Abrir, Guardar, Ejecutar y Reportes; editor con números de línea; consola; pestañas de Errores, Tabla de símbolos y AST.

Atajos:

```text
Ctrl + S
Ctrl + O
Ctrl + Enter
```

## 13. Generación de código a bajo nivel

La implementación es un intérprete, no un compilador que emite ensamblador o código máquina.

No se genera código de bajo nivel como producto final. La representación intermedia es el AST, y el runtime evalúa directamente sus nodos.

## 14. Decisiones de diseño

- AST mediante jerarquía de clases.
- Scopes con entornos encadenados.
- Errores acumulables.
- Separación entre semántica y runtime.
- Reportes desacoplados del intérprete.
- API REST separada de la GUI.

## 15. Desafíos

- precedencia y postfix;
- recuperación de errores sintácticos;
- scopes y shadowing;
- tipos estáticos e inferencia;
- valores por defecto;
- loops etiquetados;
- arrays/slices y límites;
- structs anidados;
- propagación de retorno;
- cortocircuito lógico;
- generación Graphviz;
- integración Django.

## 16. Pruebas

```bash
python -m pytest -v
```

La suite cubre lexer, parser, semántica, runtime, reportes, API, GUI e integración.

El fixture de prueba amplia es:

```text
tests/fixtures/prueba_auxiliar.ox
```
