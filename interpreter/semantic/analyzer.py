from interpreter.errors import ErrorList

from interpreter.ast.nodes import (
    Program,
    FunctionDecl,
    StructDecl,
    VarDeclaration,
    Assignment,
    CompoundAssignment,
    Literal,
    Identifier,
    StringFrom,
    StringNew,
    BinaryOp,
    UnaryOp,
    Comparison,
    LogicalOp,
    FunctionCall,
    IfStmt,
    WhileStmt,
    ReturnStmt,
    ExpressionStmt,
    PrintlnCall,
    Block,
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

        # Guarda los entornos creados para cada función.
        self.function_envs = {}

        # Contador para generar nombres únicos de scopes internos.
        self.scope_counter = 0
        # Función cuyo cuerpo se está analizando actualmente.
        # Se utiliza para validar sentencias return.
        self.current_function = None


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


    def _new_scope_name(self, env, kind):
        """Genera un nombre único para un ámbito interno."""

        self.scope_counter += 1

        return (
            f'{env.nombre}::'
            f'{kind}_{self.scope_counter}'
        )


    def _semantic_error(self, node, descripcion):
        """Registra un error semántico asociado a un nodo."""

        self.errors.add(
            'Semántico',
            descripcion,
            node.linea,
            node.columna,
            self._fragmento(node)
        )

    def _types_compatible(self, expected, actual):
        """
        Determina si un valor puede almacenarse en una variable
        del tipo esperado.

        Por ahora OxigenScript exige coincidencia del tipo estático.
        """

        if expected is None or actual is None:
            return True

        return expected == actual


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
        previous_function = self.current_function

        self.current_function = node

        self._analyze_block(
            node.cuerpo,
            env
        )

        self.current_function = previous_function


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

            elif isinstance(instruction, Assignment):
                self._analyze_assignment(
                    instruction,
                    env
                )

            elif isinstance(instruction, CompoundAssignment):
                self._analyze_compound_assignment(
                    instruction,
                    env
                )

            elif isinstance(instruction, IfStmt):
                self._analyze_if(
                    instruction,
                    env
                )

            elif isinstance(instruction, WhileStmt):
                self._analyze_while(
                    instruction,
                    env
                )

            elif isinstance(instruction, ReturnStmt):
                self._analyze_return(
                    instruction,
                    env
                )

            elif isinstance(instruction, ExpressionStmt):
                self._infer_type(
                    instruction.expresion,
                    env
                )


    def _analyze_if(self, node, env):
        """Analiza condición y ámbitos de una sentencia if."""

        condition_type = self._infer_type(
            node.condicion,
            env
        )

        if (
            condition_type is not None
            and condition_type != 'bool'
        ):
            self._semantic_error(
                node.condicion,
                (
                    'La condición de una sentencia if '
                    'debe ser de tipo bool, '
                    f'no {self._type_to_string(condition_type)}.'
                )
            )

        then_env = env.create_child(
            self._new_scope_name(
                env,
                'if'
            )
        )

        self._analyze_block(
            node.cuerpo,
            then_env
        )

        if node.else_branch is None:
            return

        # else { ... }
        if isinstance(node.else_branch, Block):

            else_env = env.create_child(
                self._new_scope_name(
                    env,
                    'else'
                )
            )

            self._analyze_block(
                node.else_branch,
                else_env
            )

        # else if ...
        elif isinstance(node.else_branch, IfStmt):
            self._analyze_if(
                node.else_branch,
                env
            )


    def _analyze_while(self, node, env):
        """Analiza condición y cuerpo de un while."""

        condition_type = self._infer_type(
            node.condicion,
            env
        )

        if (
            condition_type is not None
            and condition_type != 'bool'
        ):
            self._semantic_error(
                node.condicion,
                (
                    'La condición de una sentencia while '
                    'debe ser de tipo bool, '
                    f'no {self._type_to_string(condition_type)}.'
                )
            )

        while_env = env.create_child(
            self._new_scope_name(
                env,
                'while'
            )
        )

        self._analyze_block(
            node.cuerpo,
            while_env
        )


    def _analyze_return(self, node, env):
        """Valida una sentencia return."""

        function = self.current_function

        if function is None:
            self._semantic_error(
                node,
                "La sentencia return debe encontrarse dentro de una función."
            )
            return

        expected_type = function.tipo_retorno

        # -----------------------------------------------------
        # return;
        # -----------------------------------------------------

        if node.valor is None:

            if expected_type is not None:
                self._semantic_error(
                    node,
                    (
                        f"La función '{function.nombre}' "
                        f"debe retornar un valor de tipo "
                        f"{self._type_to_string(expected_type)}."
                    )
                )

            return

        # -----------------------------------------------------
        # return expresion;
        # -----------------------------------------------------

        actual_type = self._infer_type(
            node.valor,
            env
        )

        # Función sin tipo de retorno declarado.
        if expected_type is None:

            self._semantic_error(
                node,
                (
                    f"La función '{function.nombre}' "
                    "no debe retornar un valor."
                )
            )

            return

        # Si la propia expresión ya produjo un error,
        # evitamos generar otro error en cascada.
        if actual_type is None:
            return

        if not self._types_compatible(
            expected_type,
            actual_type
        ):
            self._semantic_error(
                node,
                (
                    f"La función '{function.nombre}' "
                    f"debe retornar un valor de tipo "
                    f"{self._type_to_string(expected_type)}, "
                    f"pero se obtuvo "
                    f"{self._type_to_string(actual_type)}."
                )
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
            and not self._types_compatible(
                declared_type,
                inferred_type
            )
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


    def _analyze_assignment(self, node, env):
        """
        Analiza una asignación simple:

            x = expresion;

        Por ahora se validan targets Identifier.
        FieldAccess y ArrayAccess se analizarán
        con structs y arreglos.
        """

        # Siempre analizamos el RHS para no ocultar
        # posibles errores dentro de la expresión.
        value_type = self._infer_type(
            node.valor,
            env
        )

        if not isinstance(node.target, Identifier):
            return

        symbol = env.lookup(
            node.target.nombre
        )

        # -----------------------------------------------------
        # Variable inexistente
        # -----------------------------------------------------

        if symbol is None:
            self._semantic_error(
                node.target,
                (
                    f"La variable '{node.target.nombre}' "
                    "no ha sido declarada."
                )
            )
            return

        # -----------------------------------------------------
        # El identificador existe pero no es variable
        # -----------------------------------------------------

        if symbol.categoria not in (
            'variable',
            'parametro',
        ):
            self._semantic_error(
                node.target,
                (
                    f"El identificador '{node.target.nombre}' "
                    "no es una variable asignable."
                )
            )
            return

        # -----------------------------------------------------
        # Mutabilidad
        # -----------------------------------------------------

        if not symbol.mutable:
            self._semantic_error(
                node.target,
                (
                    f"No es posible modificar la variable "
                    f"'{node.target.nombre}' porque fue "
                    "declarada como inmutable."
                )
            )
            return

        # -----------------------------------------------------
        # Compatibilidad de tipo
        # -----------------------------------------------------

        if not self._types_compatible(
            symbol.tipo,
            value_type
        ):
            self._semantic_error(
                node,
                (
                    f"No es posible asignar un valor de tipo "
                    f"{self._type_to_string(value_type)} "
                    f"a una variable de tipo "
                    f"{self._type_to_string(symbol.tipo)}."
                )
            )


    def _analyze_compound_assignment(self, node, env):
        """
        Analiza:

            +=
            -=
            *=
            /=
            %=
        """

        if not isinstance(node.target, Identifier):
            # Analizamos al menos la expresión derecha.
            self._infer_type(
                node.valor,
                env
            )
            return

        symbol = env.lookup(
            node.target.nombre
        )

        # -----------------------------------------------------
        # Variable inexistente
        # -----------------------------------------------------

        if symbol is None:
            self._semantic_error(
                node.target,
                (
                    f"La variable '{node.target.nombre}' "
                    "no ha sido declarada."
                )
            )

            # También analizamos RHS.
            self._infer_type(
                node.valor,
                env
            )

            return

        # -----------------------------------------------------
        # Debe ser variable o parámetro
        # -----------------------------------------------------

        if symbol.categoria not in (
            'variable',
            'parametro',
        ):
            self._semantic_error(
                node.target,
                (
                    f"El identificador '{node.target.nombre}' "
                    "no es una variable asignable."
                )
            )

            self._infer_type(
                node.valor,
                env
            )

            return

        # -----------------------------------------------------
        # Mutabilidad
        # -----------------------------------------------------

        if not symbol.mutable:
            self._semantic_error(
                node.target,
                (
                    f"No es posible modificar la variable "
                    f"'{node.target.nombre}' porque fue "
                    "declarada como inmutable."
                )
            )

            # Aun así analizamos RHS.
            self._infer_type(
                node.valor,
                env
            )

            return

        # -----------------------------------------------------
        # Convertir += en +, -= en -, etc.
        # -----------------------------------------------------

        operators = {
            '+=': '+',
            '-=': '-',
            '*=': '*',
            '/=': '/',
            '%=': '%',
        }

        arithmetic_operator = operators.get(
            node.op
        )

        if arithmetic_operator is None:
            self._semantic_error(
                node,
                (
                    f"Operador de asignación compuesto "
                    f"desconocido: '{node.op}'."
                )
            )
            return

        # x += y equivale semánticamente a comprobar:
        #
        # x + y
        #
        # y después verificar si ese resultado puede
        # almacenarse nuevamente en x.

        operation = BinaryOp(
            node.target,
            arithmetic_operator,
            node.valor,
            node.linea,
            node.columna
        )

        result_type = self._infer_binary(
            operation,
            env
        )

        if result_type is None:
            return

        if not self._types_compatible(
            symbol.tipo,
            result_type
        ):
            self._semantic_error(
                node,
                (
                    f"El resultado de '{node.op}' es de tipo "
                    f"{self._type_to_string(result_type)} "
                    f"y no puede almacenarse en una variable "
                    f"de tipo {self._type_to_string(symbol.tipo)}."
                )
            )


    # =========================================================
    # INFERENCIA DE TIPOS
    # =========================================================


    def _infer_type(self, expression, env):
        """
        Determina el tipo de una expresión y registra
        errores semánticos cuando corresponde.
        """

        if expression is None:
            return None

        # -----------------------------------------------------
        # Literales
        # -----------------------------------------------------

        if isinstance(expression, Literal):
            return expression.tipo

        # -----------------------------------------------------
        # String
        # -----------------------------------------------------

        if isinstance(expression, StringFrom):
            return 'String'

        if isinstance(expression, StringNew):
            return 'String'

        # -----------------------------------------------------
        # Llamadas a funciones
        # -----------------------------------------------------

        if isinstance(expression, FunctionCall):
            return self._infer_function_call(
                expression,
                env
            )

        # -----------------------------------------------------
        # Identificadores
        # -----------------------------------------------------

        if isinstance(expression, Identifier):

            symbol = env.lookup(
                expression.nombre
            )

            if symbol is None:
                self._semantic_error(
                    expression,
                    (
                        f"La variable '{expression.nombre}' "
                        'no ha sido declarada.'
                    )
                )

                return None

            return symbol.tipo

        # -----------------------------------------------------
        # Aritmética
        # -----------------------------------------------------

        if isinstance(expression, BinaryOp):
            return self._infer_binary(
                expression,
                env
            )

        # -----------------------------------------------------
        # Unarios
        # -----------------------------------------------------

        if isinstance(expression, UnaryOp):
            return self._infer_unary(
                expression,
                env
            )

        # -----------------------------------------------------
        # Comparación
        # -----------------------------------------------------

        if isinstance(expression, Comparison):
            return self._infer_comparison(
                expression,
                env
            )

        # -----------------------------------------------------
        # Lógicos
        # -----------------------------------------------------

        if isinstance(expression, LogicalOp):
            return self._infer_logical(
                expression,
                env
            )

        # -----------------------------------------------------
        # println!
        # -----------------------------------------------------

        if isinstance(expression, PrintlnCall):

            for argument in expression.argumentos:
                self._infer_type(
                    argument,
                    env
                )

            # println! produce un efecto,
            # no un valor de OxigenScript.
            return None

        return None


    def _infer_binary(self, expression, env):
        """Obtiene el tipo resultante de una operación aritmética."""

        left_type = self._infer_type(
            expression.izq,
            env
        )

        right_type = self._infer_type(
            expression.der,
            env
        )

        # Evitar errores en cascada.
        if left_type is None or right_type is None:
            return None

        operator = expression.op

        numeric_types = {
            'i32',
            'f64',
        }

        # -----------------------------------------------------
        # Operaciones numéricas
        # -----------------------------------------------------

        if (
            left_type in numeric_types
            and right_type in numeric_types
        ):
            if (
                left_type == 'f64'
                or right_type == 'f64'
            ):
                return 'f64'

            return 'i32'

        # -----------------------------------------------------
        # String + String
        # -----------------------------------------------------

        if (
            operator == '+'
            and left_type == 'String'
            and right_type == 'String'
        ):
            return 'String'

        # -----------------------------------------------------
        # Repetición de String
        # -----------------------------------------------------

        if operator == '*':

            if (
                left_type == 'String'
                and right_type == 'i32'
            ):
                return 'String'

            if (
                left_type == 'i32'
                and right_type == 'String'
            ):
                return 'String'

        # -----------------------------------------------------
        # Operación inválida
        # -----------------------------------------------------

        self._semantic_error(
            expression,
            (
                f"No es posible aplicar el operador "
                f"'{operator}' entre los tipos "
                f"{self._type_to_string(left_type)} y "
                f"{self._type_to_string(right_type)}."
            )
        )

        return None


    def _infer_unary(self, expression, env):
        """Valida operadores unarios."""

        operand_type = self._infer_type(
            expression.operando,
            env
        )

        if operand_type is None:
            return None

        # Negación numérica.
        if expression.op == '-':

            if operand_type in ('i32', 'f64'):
                return operand_type

            self._semantic_error(
                expression,
                (
                    "No es posible aplicar el operador '-' "
                    f"al tipo {self._type_to_string(operand_type)}."
                )
            )

            return None

        # NOT lógico.
        if expression.op == '!':

            if operand_type == 'bool':
                return 'bool'

            self._semantic_error(
                expression,
                (
                    "No es posible aplicar el operador '!' "
                    f"al tipo {self._type_to_string(operand_type)}."
                )
            )

            return None

        return None


    def _infer_comparison(self, expression, env):
        """Valida operadores relacionales."""

        left_type = self._infer_type(
            expression.izq,
            env
        )

        right_type = self._infer_type(
            expression.der,
            env
        )

        if left_type is None or right_type is None:
            return None

        compatible_pairs = {
            ('i32', 'i32'),
            ('i32', 'f64'),
            ('f64', 'i32'),
            ('f64', 'f64'),

            ('bool', 'bool'),

            ('char', 'char'),
            ('i32', 'char'),
            ('char', 'i32'),

            ('String', 'String'),
        }

        if (
            left_type,
            right_type
        ) in compatible_pairs:
            return 'bool'

        self._semantic_error(
            expression,
            (
                f"No es posible aplicar el operador "
                f"'{expression.op}' entre los tipos "
                f"{self._type_to_string(left_type)} y "
                f"{self._type_to_string(right_type)}."
            )
        )

        return None


    def _infer_logical(self, expression, env):
        """Valida && y ||."""

        left_type = self._infer_type(
            expression.izq,
            env
        )

        right_type = self._infer_type(
            expression.der,
            env
        )

        if left_type is None or right_type is None:
            return None

        if (
            left_type == 'bool'
            and right_type == 'bool'
        ):
            return 'bool'

        self._semantic_error(
            expression,
            (
                f"No es posible aplicar el operador "
                f"'{expression.op}' entre los tipos "
                f"{self._type_to_string(left_type)} y "
                f"{self._type_to_string(right_type)}."
            )
        )

        return None

    
    def _infer_function_call(self, expression, env):
        """Valida una llamada a una función definida por el usuario."""

        # Analizamos siempre los argumentos para poder reportar
        # errores internos aunque la llamada también sea inválida.
        argument_types = [
            self._infer_type(argument, env)
            for argument in expression.argumentos
        ]

        # Las funciones están registradas en global.
        symbol = self.global_env.lookup_local(
            expression.nombre
        )

        # -----------------------------------------------------
        # Función inexistente
        # -----------------------------------------------------

        if symbol is None:
            self._semantic_error(
                expression,
                (
                    f"La función '{expression.nombre}' "
                    "no ha sido declarada."
                )
            )

            return None

        # -----------------------------------------------------
        # Existe el nombre, pero no corresponde a una función
        # -----------------------------------------------------

        if symbol.categoria != 'funcion':
            self._semantic_error(
                expression,
                (
                    f"El identificador '{expression.nombre}' "
                    "no corresponde a una función."
                )
            )

            return None

        function = symbol.valor
        parameters = function.params

        # -----------------------------------------------------
        # Número de argumentos
        # -----------------------------------------------------

        if len(expression.argumentos) != len(parameters):
            self._semantic_error(
                expression,
                (
                    f"La función '{expression.nombre}' "
                    f"esperaba {len(parameters)} argumentos, "
                    f"pero recibió {len(expression.argumentos)}."
                )
            )

        # -----------------------------------------------------
        # Tipos de argumentos
        # -----------------------------------------------------

        for parameter, actual_type in zip(
            parameters,
            argument_types
        ):

            # El argumento ya produjo otro error.
            if actual_type is None:
                continue

            if not self._types_compatible(
                parameter.tipo,
                actual_type
            ):
                self._semantic_error(
                    expression,
                    (
                        f"La función '{expression.nombre}' "
                        f"esperaba un argumento de tipo "
                        f"{self._type_to_string(parameter.tipo)} "
                        f"para el parámetro '{parameter.nombre}', "
                        f"pero recibió "
                        f"{self._type_to_string(actual_type)}."
                    )
                )

        # Aunque haya un error de argumentos, conocemos
        # estáticamente el tipo que retorna la función.
        return function.tipo_retorno


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