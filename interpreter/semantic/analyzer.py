from interpreter.errors import ErrorList

from interpreter.ast.nodes import (
    Program,
    FunctionDecl,
    StructDecl,
    VarDeclaration,
    Literal,
    Identifier,
    StringFrom,
    StringNew,
)

from interpreter.semantic.environment import Environment
from interpreter.semantic.symbol import Symbol
from interpreter.semantic.symbol_table import SymbolTable


class SemanticAnalyzer:
    """Analizador semántico de OxigenScript."""

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

        # Nos permitirá consultar los entornos de las funciones
        # durante pruebas y etapas posteriores.
        self.function_envs = {}

    # =========================================================
    # UTILIDADES
    # =========================================================

    def _fragmento(self, nodo):
        """Obtiene la línea fuente correspondiente a un nodo."""

        if not self.source_lines:
            return ''

        linea = getattr(nodo, 'linea', 0)

        if linea <= 0 or linea > len(self.source_lines):
            return ''

        return self.source_lines[linea - 1]

    def _primer_fragmento_util(self):
        """Obtiene la primera línea no vacía del código."""

        for line in self.source_lines:
            if line.strip():
                return line

        return ''

    # =========================================================
    # ENTRADA PRINCIPAL
    # =========================================================

    def analyze(self, ast):
        """Ejecuta el análisis semántico."""

        if ast is None:
            return self.global_env

        if not isinstance(ast, Program):
            raise TypeError(
                'SemanticAnalyzer esperaba un nodo Program.'
            )

        # Primera pasada:
        # funciones y structs deben conocerse antes
        # de analizar cualquier cuerpo.
        self._register_globals(ast)

        # Validaciones globales.
        self._validate_main(ast)

        # Segunda pasada:
        # parámetros y cuerpos de funciones.
        self._analyze_functions(ast)

        return self.global_env

    # =========================================================
    # PRIMERA PASADA: DECLARACIONES GLOBALES
    # =========================================================

    def _register_globals(self, program):
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

    # =========================================================
    # VALIDACIÓN DE MAIN
    # =========================================================

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

        # Si existen varias main, define() ya reportó
        # la redeclaración global.

    # =========================================================
    # SEGUNDA PASADA: FUNCIONES
    # =========================================================

    def _analyze_functions(self, program):
        for declaration in program.declaraciones:

            if isinstance(declaration, FunctionDecl):
                self._analyze_function(declaration)

    def _analyze_function(self, node):
        """
        Crea el scope de la función y registra parámetros
        antes de analizar sus instrucciones.
        """

        env = self.global_env.create_child(
            node.nombre
        )

        # Conservamos el primer entorno asociado al nombre.
        # Los duplicados globales ya fueron reportados.
        if node.nombre not in self.function_envs:
            self.function_envs[node.nombre] = env

        # Parámetros.
        for param in node.params:

            symbol = Symbol(
                nombre=param.nombre,
                tipo=param.tipo,
                categoria='parametro',
                mutable=False,
                valor=None,
                linea=param.linea,
                columna=param.columna
            )

            env.define(
                symbol,
                self._fragmento(param)
            )

        # Cuerpo.
        self._analyze_block(
            node.cuerpo,
            env
        )

    # =========================================================
    # BLOQUES E INSTRUCCIONES
    # =========================================================

    def _analyze_block(self, block, env):
        for instruction in block.instrucciones:

            if isinstance(instruction, VarDeclaration):
                self._analyze_var_declaration(
                    instruction,
                    env
                )

    # =========================================================
    # VARIABLES
    # =========================================================

    def _analyze_var_declaration(self, node, env):
        """
        Analiza una declaración de variable.

        Por ahora:
        - determina su tipo
        - verifica incompatibilidad básica
        - registra la variable
        - permite shadowing
        """

        declared_type = node.tipo

        inferred_type = None

        if node.valor is not None:
            inferred_type = self._infer_type(
                node.valor,
                env
            )

        # Si no existe tipo explícito, intentamos inferirlo.
        final_type = declared_type

        if final_type is None:
            final_type = inferred_type

        # Si hay tipo explícito y podemos determinar
        # el tipo del valor, deben coincidir.
        if (
            declared_type is not None
            and inferred_type is not None
            and declared_type != inferred_type
        ):
            self.errors.add(
                'Semántico',
                (
                    f"No es posible asignar un valor de tipo "
                    f"{self._type_to_string(inferred_type)} "
                    f"a una variable de tipo "
                    f"{self._type_to_string(declared_type)}."
                ),
                node.linea,
                node.columna,
                self._fragmento(node)
            )

        symbol = Symbol(
            nombre=node.nombre,
            tipo=final_type,
            categoria='variable',
            mutable=node.mutable,
            valor=self._literal_value(node.valor),
            linea=node.linea,
            columna=node.columna
        )

        # OxigenScript permite shadowing de variables.
        env.define(
            symbol,
            self._fragmento(node),
            allow_shadowing=True
        )

    # =========================================================
    # INFERENCIA DE TIPOS
    # =========================================================

    def _infer_type(self, expression, env):
        """
        Infiere tipos simples.

        Todavía NO analiza operaciones binarias,
        llamadas, arrays, etc.
        """

        if expression is None:
            return None

        if isinstance(expression, Literal):
            return expression.tipo

        if isinstance(expression, StringFrom):
            return 'String'

        if isinstance(expression, StringNew):
            return 'String'

        if isinstance(expression, Identifier):
            symbol = env.lookup(
                expression.nombre
            )

            if symbol is not None:
                return symbol.tipo

            return None

        return None

    # =========================================================
    # UTILIDADES DE TIPOS
    # =========================================================

    def _type_to_string(self, tipo):
        if tipo is None:
            return 'desconocido'

        if (
            isinstance(tipo, tuple)
            and len(tipo) == 3
            and tipo[0] == 'array'
        ):
            return (
                f'[{self._type_to_string(tipo[1])}; '
                f'{tipo[2]}]'
            )

        return str(tipo)

    def _literal_value(self, expression):
        """
        Conserva el valor directamente cuando la inicialización
        consiste en un literal.
        """

        if isinstance(expression, Literal):
            return expression.valor

        if isinstance(expression, StringFrom):
            if isinstance(expression.argumento, Literal):
                return expression.argumento.valor

        if isinstance(expression, StringNew):
            return ''

        return None


def analyze(ast, errors=None, source_code=''):
    """Función auxiliar para ejecutar el analizador semántico."""

    analyzer = SemanticAnalyzer(
        errors=errors,
        source_code=source_code
    )

    analyzer.analyze(ast)

    return analyzer