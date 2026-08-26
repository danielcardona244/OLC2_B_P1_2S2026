from interpreter.errors import ErrorList
from interpreter.ast.nodes import (
    Program,
    FunctionDecl,
    StructDecl,
)

from interpreter.semantic.environment import Environment
from interpreter.semantic.symbol import Symbol
from interpreter.semantic.symbol_table import SymbolTable


class SemanticAnalyzer:
    """
    Analizador semántico de OxigenScript.

    Esta primera etapa registra declaraciones globales:
    - funciones
    - structs

    También valida la existencia y unicidad de main.
    """

    def __init__(self, errors=None, source_code=''):
        if errors is None:
            errors = ErrorList()

        self.errors = errors
        self.source_code = source_code
        self.source_lines = source_code.splitlines()

        self.symbol_table = SymbolTable()

        self.global_env = Environment(
            nombre='global',
            errors=self.errors,
            symbol_table=self.symbol_table
        )

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------

    def _fragmento(self, nodo):
        """
        Obtiene la línea de código fuente correspondiente
        al nodo recibido.
        """

        if not self.source_lines:
            return ''

        linea = getattr(nodo, 'linea', 0)

        if linea <= 0 or linea > len(self.source_lines):
            return ''

        return self.source_lines[linea - 1]

    # ---------------------------------------------------------
    # Entrada principal
    # ---------------------------------------------------------

    def analyze(self, ast):
        """
        Ejecuta el análisis semántico sobre un Program.
        """

        if ast is None:
            return self.global_env

        if not isinstance(ast, Program):
            raise TypeError(
                'SemanticAnalyzer esperaba un nodo Program.'
            )

        # Primera pasada:
        # registrar declaraciones globales.
        self._register_globals(ast)

        # Validaciones globales.
        self._validate_main(ast)

        return self.global_env

    # ---------------------------------------------------------
    # Declaraciones globales
    # ---------------------------------------------------------

    def _register_globals(self, program):
        """
        Registra funciones y structs antes de analizar cuerpos.

        Esto permitirá posteriormente llamar funciones aunque
        estén declaradas después de la función que las utiliza.
        """

        for declaration in program.declaraciones:

            if isinstance(declaration, FunctionDecl):
                self._register_function(declaration)

            elif isinstance(declaration, StructDecl):
                self._register_struct(declaration)

    def _register_function(self, node):
        symbol = Symbol(
            nombre=node.nombre,
            tipo=node.tipo_retorno,
            categoria='funcion',
            mutable=False,
            valor=node,
            linea=node.linea,
            columna=node.columna
        )

        self.global_env.define(
            symbol,
            self._fragmento(node)
        )

    def _register_struct(self, node):
        symbol = Symbol(
            nombre=node.nombre,
            tipo=node.nombre,
            categoria='struct',
            mutable=False,
            valor=node,
            linea=node.linea,
            columna=node.columna
        )

        self.global_env.define(
            symbol,
            self._fragmento(node)
        )

    # ---------------------------------------------------------
    # main
    # ---------------------------------------------------------

    def _validate_main(self, program):
        funciones_main = [
            declaration
            for declaration in program.declaraciones
            if isinstance(declaration, FunctionDecl)
            and declaration.nombre == 'main'
        ]

        if len(funciones_main) == 0:
            self.errors.add(
                'Semántico',
                "El programa debe definir una función 'main'.",
                1,
                1,
                self._primer_fragmento_util()
            )

        # Si existen dos o más main, Environment.define()
        # ya reporta la redeclaración de la segunda y siguientes.
        # No agregamos otro error aquí para evitar duplicados.

    def _primer_fragmento_util(self):
        """Devuelve la primera línea no vacía del código fuente."""

        for line in self.source_lines:
            if line.strip():
                return line

        return ''


def analyze(ast, errors=None, source_code=''):
    """
    Función auxiliar para ejecutar el analizador semántico.
    """

    analyzer = SemanticAnalyzer(
        errors=errors,
        source_code=source_code
    )

    analyzer.analyze(ast)

    return analyzer