# OLC2_B_P1_2S2026

Proyecto 1 de **Organización de Lenguajes y Compiladores 2** — Segundo Semestre 2026.

## OxigenScript

OxigenScript es un intérprete web desarrollado en **Python**, **PLY** y **Django**. Permite escribir o abrir código fuente, analizarlo, ejecutarlo y consultar los reportes generados.

### Funcionalidades principales

- Análisis léxico con PLY.
- Análisis sintáctico y construcción de AST.
- Análisis semántico con validación de tipos, ámbitos y tabla de símbolos.
- Ejecución a partir de `main`.
- Variables, tipos primitivos, arreglos, slices, structs y funciones.
- Expresiones aritméticas, relacionales y lógicas.
- `if`, `while`, `loop`, `match`, `break`, `continue` y `return`.
- Funciones embebidas y métodos.
- Reporte de errores.
- Tabla de símbolos.
- AST gráfico mediante Graphviz.
- Interfaz web con editor, consola y pestañas de reportes.

## Requisitos

- Linux.
- Python 3.12 o compatible.
- Graphviz.
- Dependencias de `requirements.txt`.

En Ubuntu/Debian:

```bash
sudo apt update
sudo apt install graphviz
```

## Instalación

```bash
git clone https://github.com/danielcardona244/OLC2_B_P1_2S2026.git
cd OLC2_B_P1_2S2026

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Ejecución

```bash
python manage.py runserver 127.0.0.1:7810
```

Abrir:

```text
http://127.0.0.1:7810/
```

## Pruebas

```bash
python manage.py check
python -m pytest -v
```

## Estructura

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
│   ├── diagrams/
│   └── images/
├── manage.py
├── requirements.txt
└── README.md
```

## Documentación

- [Documentación técnica](docs/DOCUMENTACION_TECNICA.md)
- [Manual de usuario](docs/MANUAL_USUARIO.md)
- [Diagrama de clases](docs/diagrams/diagrama_clases.md)
- [Flujo de procesamiento](docs/diagrams/flujo_procesamiento.md)
- [Checklist de entrega](docs/CHECKLIST_ENTREGA.md)

## Puerto

El proyecto utiliza `127.0.0.1:7810`. El número 7810 fue elegido en referencia al código 0781 del curso.
