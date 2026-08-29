# Documentación Técnica — OxigenScript IDE

## 1. Descripción general

OxigenScript IDE es un intérprete web desarrollado en Python para procesar programas escritos en OxigenScript. La solución implementa análisis léxico, análisis sintáctico, construcción de AST, análisis semántico, ejecución y generación de reportes.

La aplicación utiliza una arquitectura monolítica cliente/servidor con Django.

---

## 2. Tecnologías utilizadas

| Área | Tecnología |
|---|---|
| Lenguaje principal | Python |
| Análisis léxico | PLY Lex |
| Análisis sintáctico | PLY Yacc |
| Backend web | Django |
| Frontend | HTML, CSS, JavaScript |
| AST gráfico | Graphviz |
| Pruebas | pytest |
| Sistema operativo | Linux |

---

## 3. Arquitectura general

```text
GUI
 ↓
API Django
 ↓
Lexer
 ↓
Parser
 ↓
AST
 ↓
Análisis semántico
 ↓
Runtime
 ↓
Reportes
 ↓
Respuesta a GUI
```

Diagramas complementarios:

- [Arquitectura general](diagrams/arquitectura_general.svg)
- [Clases principales del backend](diagrams/clases_backend.svg)
- [Jerarquía del AST](diagrams/clases_ast.md)


---

## 4. Estructura del proyecto

```text
OLC2_B_P1_2S2026/
├── interpreter/
│   ├── ast/
│   ├── lexer/
│   ├── parser/
│   ├── semantic/
│   ├── runtime/
│   └── reports/
├── tests/
│   ├── fixtures/
│   ├── integration/
│   ├── lexer/
│   ├── parser/
│   ├── semantic/
│   ├── runtime/
│   ├── reports/
│   └── web/
├── web/
│   ├── api/
│   ├── static/
│   └── templates/
├── docs/
├── manage.py
├── requirements.txt
└── README.md
```

---

## 5. Analizador léxico

Archivo principal:

```text
interpreter/lexer/lexer.py
```

Responsabilidades:

- palabras reservadas;
- identificadores;
- enteros y flotantes;
- strings y chars;
- operadores;
- delimitadores;
- comentarios;
- línea y columna;
- errores léxicos.

Tipos principales:

```text
i32
f64
bool
char
String
[T; N]
```

---

## 6. Analizador sintáctico

Archivo:

```text
interpreter/parser/parser.py
```

Responsabilidades:

- producciones PLY;
- precedencia;
- construcción del AST;
- recuperación ante errores sintácticos;
- integración con `ErrorList`.

Construcciones soportadas:

- funciones;
- structs;
- variables;
- asignaciones;
- expresiones;
- `if`, `while`, `loop`, `match`;
- `return`, `break`, `continue`;
- arrays y slices;
- llamadas a funciones y métodos.

---

## 7. Gramática formal resumida

### Identificadores

```text
<identifier> ::= (<letter> | "_") (<letter> | <digit> | "_")*
```

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
<param> ::= <identifier> ":" <type>
```

### Bloques

```text
<block> ::= "{" <stmt_list> "}"
```

### Control

```text
<if_stmt> ::= if <expression> <block> <else_opt>
<while_stmt> ::= while <expression> <block>
<loop_stmt> ::= <label_opt> loop <block>
<match_stmt> ::= match <expression> "{" <match_arms> "}"
```

---

## 8. AST

Archivo:

```text
interpreter/ast/nodes.py
```

Nodos principales:

```text
Program
FunctionDecl
Param
StructDecl
StructField
VarDeclaration
Assignment
CompoundAssignment
IfStmt
WhileStmt
LoopStmt
MatchStmt
MatchArm
Block
ReturnStmt
BreakStmt
ContinueStmt
ExpressionStmt
Literal
Identifier
BinaryOp
UnaryOp
Comparison
LogicalOp
ArrayLiteral
ArrayRepeat
ArrayAccess
SliceAccess
FieldAccess
FunctionCall
MethodCall
StringFrom
StringNew
PrintlnCall
StructInit
```

El AST es utilizado por el análisis semántico, el runtime y el reporte Graphviz.

---

## 9. Análisis semántico

Módulos:

```text
interpreter/semantic/analyzer.py
interpreter/semantic/environment.py
interpreter/semantic/symbol.py
interpreter/semantic/symbol_table.py
```

Valida:

- declaraciones;
- existencia de identificadores;
- mutabilidad;
- compatibilidad de tipos;
- scopes y shadowing;
- parámetros;
- llamadas a funciones;
- retornos;
- arrays y slices;
- structs;
- control de flujo;
- existencia y unicidad de `main`.

---

## 10. Tabla de símbolos

Registra variables, parámetros, funciones y structs.

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

Con errores recuperables, el análisis semántico puede conservar una tabla parcial.

---

## 11. Runtime

Módulos:

```text
interpreter/runtime/environment.py
interpreter/runtime/interpreter.py
interpreter/runtime/runner.py
interpreter/runtime/signals.py
interpreter/runtime/value.py
```

Responsabilidades:

- registrar funciones y structs;
- localizar `main`;
- ejecutar instrucciones;
- evaluar expresiones;
- administrar scopes en ejecución;
- manejar variables y mutabilidad;
- producir salida de consola.

---

## 12. Señales de transferencia

Para implementar `return`, `break` y `continue` se utilizan señales internas que permiten transferir el control entre nodos y ciclos anidados.

---

## 13. Operaciones y builtins

Aritméticos:

```text
+ - * / %
```

Relacionales:

```text
== != > >= < <=
```

Lógicos:

```text
&& || !
```

Funciones/métodos:

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

---

## 14. Manejo de errores

Los errores se centralizan en `ErrorList` y almacenan:

- tipo;
- descripción;
- línea;
- columna;
- fragmento.

Tipos:

```text
Léxico
Sintáctico
Semántico
```

El sistema intenta recuperarse ante errores no críticos para continuar el análisis cuando sea seguro.

---

## 15. Pipeline principal

Archivo:

```text
interpreter/runtime/runner.py
```

Flujo:

```text
1. crear ErrorList
2. parsear código
3. si existe AST:
      ejecutar análisis semántico
4. si existe AST y no hay errores:
      ejecutar runtime
5. generar reportes
6. devolver resultado
```

Esto permite generar símbolos parciales ante errores recuperables sin ejecutar un programa inválido.

---

## 16. Reportes

Módulos:

```text
interpreter/reports/common.py
interpreter/reports/error_report.py
interpreter/reports/symbol_report.py
interpreter/reports/ast_report.py
interpreter/reports/manager.py
```

Salidas:

```text
reports/errors/errores.html
reports/symbols/tabla_simbolos.html
reports/ast/ast.dot
reports/ast/ast.svg
```

---

## 17. API REST

Módulos:

```text
web/api/views.py
web/api/urls.py
```

Endpoints:

```text
GET  /api/health/
POST /api/execute/
GET  /api/reports/errors/
GET  /api/reports/symbols/
GET  /api/reports/ast/
```

---

## 18. GUI

Archivos:

```text
web/templates/index.html
web/static/css/app.css
web/static/js/app.js
web/views.py
web/urls.py
```

Funciones:

- editar;
- abrir;
- guardar;
- ejecutar;
- mostrar consola;
- mostrar errores;
- mostrar símbolos;
- mostrar AST;
- abrir AST en otra pestaña.

---

## 19. Generación de código a bajo nivel

OxigenScript fue implementado como **intérprete**, no como compilador que emite código máquina o ensamblador.

Por ello, la representación intermedia utilizada es el AST y el runtime evalúa directamente sus nodos.

---

## 20. Decisiones de diseño

- AST con clases propias.
- scopes mediante entornos enlazados.
- lista compartida de errores.
- separación entre semántica y runtime.
- reportes desacoplados del intérprete.
- GUI desacoplada mediante API REST.

---

## 21. Correcciones finales de integración

Durante la estabilización final se incorporaron:

- corrección de la ruta principal `/` en Django;
- mejoras en la integración GUI/API;
- apertura del AST en pestaña independiente;
- mejora visual del botón del AST;
- generación de tabla de símbolos parcial con errores recuperables;
- bloqueo del runtime cuando existen errores;
- pruebas adicionales de reportes y GUI.

---

## 22. Pruebas

Suite:

```text
tests/lexer/
tests/parser/
tests/semantic/
tests/runtime/
tests/reports/
tests/web/
tests/integration/
```

Fixture amplio:

```text
tests/fixtures/prueba_auxiliar.ox
```

Comando:

```bash
python -m pytest -v
```

Estado alcanzado durante la estabilización final:

```text
364 passed
```

---

## 23. Desafíos principales

- precedencia y postfix;
- recuperación sintáctica;
- scopes y shadowing;
- inferencia y validación de tipos;
- valores por defecto;
- loops etiquetados;
- arrays y slices;
- structs anidados;
- propagación de `return`;
- cortocircuito lógico;
- generación Graphviz;
- integración Django;
- conservación de información semántica después de errores recuperables.

---

## 24. Conclusión

OxigenScript IDE implementa un pipeline completo desde el código fuente hasta la ejecución y generación de reportes. Su separación modular entre lexer, parser, AST, semántica, runtime, reportes y capa web facilita el mantenimiento, las pruebas y la extensión del sistema.
