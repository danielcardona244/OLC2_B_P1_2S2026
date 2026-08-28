from interpreter.errors import ErrorList
from interpreter.parser.parser import parse
from interpreter.semantic.analyzer import SemanticAnalyzer
from interpreter.runtime.interpreter import Interpreter


def run_source(source_code):
    """
    Ejecuta el pipeline completo:
    parser -> semántica -> runtime.

    Devuelve un diccionario útil para la futura API REST.
    """

    errors = ErrorList()

    ast = parse(
        source_code,
        errors,
    )

    analyzer = None
    runtime = None
    output = ''

    if (
        ast is not None
        and not errors.has_errors()
    ):
        analyzer = SemanticAnalyzer(
            errors=errors,
            source_code=source_code,
        )

        analyzer.analyze(
            ast
        )

    if (
        ast is not None
        and not errors.has_errors()
    ):
        runtime = Interpreter(
            errors=errors,
            source_code=source_code,
        )

        output = runtime.execute(
            ast
        )

    return {
        'ast': ast,
        'analyzer': analyzer,
        'runtime': runtime,
        'errors': errors,
        'output': output,
    }
