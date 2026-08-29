from interpreter.errors import ErrorList
from interpreter.parser.parser import parse
from interpreter.semantic.analyzer import SemanticAnalyzer
from interpreter.runtime.interpreter import Interpreter
from interpreter.reports.manager import ReportManager


def run_source(
    source_code,
    report_dir=None,
):
    """
    Ejecuta:
        parser -> semántica -> runtime -> reportes

    `report_dir` debe apuntar a la carpeta raíz de reportes.
    Ejemplo:
        run_source(codigo, report_dir="reports")

    Esto genera:
        reports/errors/errores.html
        reports/symbols/tabla_simbolos.html
        reports/ast/ast.dot
        reports/ast/ast.svg
    """

    errors = ErrorList()

    ast = parse(
        source_code,
        errors,
    )

    analyzer = None
    runtime = None
    output = ''

    # ---------------------------------------------------------
    # ANÁLISIS SEMÁNTICO
    #
    # Si el parser logró recuperar un AST, intentamos continuar
    # con semántica aunque existan errores léxicos/sintácticos.
    #
    # Esto permite construir una tabla de símbolos parcial.
    # ---------------------------------------------------------
    if ast is not None:
        analyzer = SemanticAnalyzer(
            errors=errors,
            source_code=source_code,
        )

        analyzer.analyze(ast)

    # ---------------------------------------------------------
    # EJECUCIÓN
    #
    # El runtime únicamente se ejecuta si todo el análisis
    # terminó sin errores.
    # ---------------------------------------------------------
    if (
        ast is not None
        and not errors.has_errors()
    ):
        runtime = Interpreter(
            errors=errors,
            source_code=source_code,
        )

        output = runtime.execute(ast)

    manager = ReportManager(
        ast=ast,
        analyzer=analyzer,
        errors=errors,
    )

    reports = manager.payload()

    report_files = (
        manager.write_all(report_dir)
        if report_dir is not None
        else {}
    )

    return {
        'ast': ast,
        'analyzer': analyzer,
        'runtime': runtime,
        'errors': errors,
        'output': output,
        'reports': reports,
        'report_files': report_files,
    }