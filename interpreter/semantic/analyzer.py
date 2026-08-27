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
    MethodCall,
    ArrayLiteral,
    ArrayRepeat,
    ArrayAccess,
    SliceAccess,
    FieldAccess,
    StructInit,
    IfStmt,
    WhileStmt,
    LoopStmt,
    MatchStmt,
    BreakStmt,
    ContinueStmt,
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

        # Pila de ciclos activos para validar break/continue y labels.
        self.loop_stack = []


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
        Determina si dos tipos son compatibles.
        """

        if expected is None or actual is None:
            return True

        # Tipos primitivos o structs.
        if (
            not isinstance(expected, tuple)
            or not isinstance(actual, tuple)
        ):
            return expected == actual

        # -----------------------------------------------------
        # Arrays
        # -----------------------------------------------------

        if (
            len(expected) == 3
            and len(actual) == 3
            and expected[0] == 'array'
            and actual[0] == 'array'
        ):
            expected_element = expected[1]
            actual_element = actual[1]

            expected_length = expected[2]
            actual_length = actual[2]

            if expected_length != actual_length:
                return False

            # Permite [] cuando existe contexto explícito:
            #
            # let x: [i32; 0] = [];
            if actual_element is None:
                return True

            return self._types_compatible(
                expected_element,
                actual_element
            )

        # -----------------------------------------------------
        # Slices
        # -----------------------------------------------------

        if (
            len(expected) == 2
            and len(actual) == 2
            and expected[0] == 'slice'
            and actual[0] == 'slice'
        ):
            return self._types_compatible(
                expected[1],
                actual[1]
            )

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
        
        self._register_globals(ast)
        self._validate_struct_definitions(ast)
        self._validate_function_signatures(ast)
        self._validate_main(ast)
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


    def _validate_struct_definitions(self, program):
        """Valida los campos declarados en los structs."""

        for declaration in program.declaraciones:

            if not isinstance(declaration, StructDecl):
                continue

            names = set()

            for field in declaration.campos:

                # Campo duplicado.
                if field.nombre in names:
                    self._semantic_error(
                        field,
                        (
                            f"El campo '{field.nombre}' está "
                            f"declarado más de una vez en el struct "
                            f"'{declaration.nombre}'."
                        )
                    )
                else:
                    names.add(field.nombre)

                # Tipo válido.
                if not self._is_valid_declared_type(field.tipo):
                    self._semantic_error(
                        field,
                        (
                            f"El tipo "
                            f"'{self._type_to_string(field.tipo)}' "
                            f"del campo '{field.nombre}' "
                            f"no ha sido declarado."
                        )
                    )


    def _is_valid_declared_type(self, tipo):
        """Determina si un tipo puede utilizarse en una declaración."""

        primitive_types = {
            'i32',
            'f64',
            'bool',
            'char',
            'String',
        }

        if tipo in primitive_types:
            return True

        if (
            isinstance(tipo, tuple)
            and len(tipo) == 3
            and tipo[0] == 'array'
        ):
            return self._is_valid_declared_type(tipo[1])

        if isinstance(tipo, str):
            symbol = self.global_env.lookup_local(tipo)

            return (
                symbol is not None
                and symbol.categoria == 'struct'
            )

        return False


    def _validate_function_signatures(self, program):
        """Valida tipos declarados en parámetros y retornos."""

        for declaration in program.declaraciones:

            if not isinstance(declaration, FunctionDecl):
                continue

            if (
                declaration.tipo_retorno is not None
                and not self._is_valid_declared_type(
                    declaration.tipo_retorno
                )
            ):
                self._semantic_error(
                    declaration,
                    (
                        f"El tipo de retorno "
                        f"'{self._type_to_string(declaration.tipo_retorno)}' "
                        f"de la función '{declaration.nombre}' "
                        "no ha sido declarado."
                    )
                )

            for param in declaration.params:
                if not self._is_valid_declared_type(param.tipo):
                    self._semantic_error(
                        param,
                        (
                            f"El tipo "
                            f"'{self._type_to_string(param.tipo)}' "
                            f"del parámetro '{param.nombre}' "
                            f"de la función '{declaration.nombre}' "
                            "no ha sido declarado."
                        )
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

            # Los parámetros reciben un valor al invocar la función.
            symbol.inicializado = True

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

            elif isinstance(instruction, LoopStmt):
                self._analyze_loop(
                    instruction,
                    env
                )

            elif isinstance(instruction, MatchStmt):
                self._analyze_match(
                    instruction,
                    env
                )

            elif isinstance(instruction, BreakStmt):
                self._analyze_break(
                    instruction
                )

            elif isinstance(instruction, ContinueStmt):
                self._analyze_continue(
                    instruction
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

        self.loop_stack.append({
            'label': None,
            'kind': 'while',
        })

        try:
            self._analyze_block(
                node.cuerpo,
                while_env
            )
        finally:
            self.loop_stack.pop()


    def _analyze_loop(self, node, env):
        """Analiza un loop y registra su etiqueta si existe."""

        loop_env = env.create_child(
            self._new_scope_name(
                env,
                'loop'
            )
        )

        self.loop_stack.append({
            'label': node.etiqueta,
            'kind': 'loop',
        })

        try:
            self._analyze_block(
                node.cuerpo,
                loop_env
            )
        finally:
            self.loop_stack.pop()


    def _analyze_break(self, node):
        """Valida break y break 'label."""

        if not self.loop_stack:
            self._semantic_error(
                node,
                "La sentencia break debe encontrarse dentro de un ciclo."
            )
            return

        if node.etiqueta is None:
            return

        if not self._has_active_loop_label(node.etiqueta):
            self._semantic_error(
                node,
                (
                    f"La etiqueta '{node.etiqueta}' utilizada en break "
                    "no corresponde a ningún loop activo."
                )
            )


    def _analyze_continue(self, node):
        """Valida continue y continue 'label."""

        if not self.loop_stack:
            self._semantic_error(
                node,
                "La sentencia continue debe encontrarse dentro de un ciclo."
            )
            return

        if node.etiqueta is None:
            return

        if not self._has_active_loop_label(node.etiqueta):
            self._semantic_error(
                node,
                (
                    f"La etiqueta '{node.etiqueta}' utilizada en continue "
                    "no corresponde a ningún loop activo."
                )
            )


    def _has_active_loop_label(self, label):
        """Indica si una etiqueta pertenece a un loop actualmente activo."""

        return any(
            item.get('label') == label
            for item in reversed(self.loop_stack)
        )


    def _analyze_match(self, node, env):
        """Valida tipos de patrones y scopes de una sentencia match."""

        subject_type = self._infer_type(
            node.expresion,
            env
        )

        wildcard_count = 0

        for arm in node.brazos:
            is_wildcard = (
                isinstance(arm.patron, Identifier)
                and arm.patron.nombre == '_'
            )

            if is_wildcard:
                wildcard_count += 1
            else:
                pattern_type = self._infer_type(
                    arm.patron,
                    env
                )

                if (
                    subject_type is not None
                    and pattern_type is not None
                    and not self._types_compatible(
                        subject_type,
                        pattern_type
                    )
                ):
                    self._semantic_error(
                        arm.patron,
                        (
                            "El patrón del match es de tipo "
                            f"{self._type_to_string(pattern_type)}, "
                            "pero la expresión evaluada es de tipo "
                            f"{self._type_to_string(subject_type)}."
                        )
                    )

            if isinstance(arm.cuerpo, Block):
                arm_env = env.create_child(
                    self._new_scope_name(
                        env,
                        'match'
                    )
                )

                self._analyze_block(
                    arm.cuerpo,
                    arm_env
                )
            else:
                self._infer_type(
                    arm.cuerpo,
                    env
                )

        # El parser ya exige al menos un wildcard. Aquí evitamos
        # más de uno, porque todos los posteriores serían inalcanzables.
        if wildcard_count > 1:
            self._semantic_error(
                node,
                "La sentencia match no puede contener más de un patrón comodín '_'."
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

        if (
            declared_type is not None
            and not self._is_valid_declared_type(declared_type)
        ):
            self._semantic_error(
                node,
                (
                    f"El tipo declarado "
                    f"'{self._type_to_string(declared_type)}' "
                    f"de la variable '{node.nombre}' "
                    "no ha sido declarado."
                )
            )

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


        if (
            declared_type is None
            and isinstance(inferred_type, tuple)
            and len(inferred_type) == 3
            and inferred_type[0] == 'array'
            and inferred_type[1] is None
        ):
            self._semantic_error(
                node,
                (
                    f"No es posible inferir el tipo del arreglo "
                    f"'{node.nombre}' porque está vacío."
                )
            )


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

        # Una variable solo se considera inicializada cuando existe
        # un valor cuyo tipo pudo determinarse correctamente.
        symbol.inicializado = (
            node.valor is not None
            and inferred_type is not None
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

        if isinstance(node.target, ArrayAccess):
            self._analyze_array_assignment(
                node,
                env,
                value_type
            )
            return

        if isinstance(node.target, FieldAccess):
            self._analyze_field_assignment(
                node,
                env,
                value_type
            )
            return

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
        # Primera inicialización
        # -----------------------------------------------------

        if not getattr(symbol, 'inicializado', True):

            if value_type is None:
                return

            if symbol.tipo is None:
                # let x; x = 10;  -> inferimos i32 aquí.
                symbol.tipo = value_type

            elif not self._types_compatible(
                symbol.tipo,
                value_type
            ):
                self._semantic_error(
                    node,
                    (
                        f"No es posible inicializar la variable "
                        f"'{node.target.nombre}' con un valor de tipo "
                        f"{self._type_to_string(value_type)}; "
                        f"se esperaba {self._type_to_string(symbol.tipo)}."
                    )
                )
                return

            symbol.inicializado = True
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

        if isinstance(node.target, ArrayAccess):
            self._analyze_array_compound_assignment(
                node,
                env
            )
            return

        if isinstance(node.target, FieldAccess):
            self._analyze_field_compound_assignment(
                node,
                env
            )
            return

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
        # Debe tener un valor previo
        # -----------------------------------------------------

        if not getattr(symbol, 'inicializado', True):
            self._semantic_error(
                node.target,
                (
                    f"La variable '{node.target.nombre}' no ha sido "
                    "inicializada y no puede utilizarse en una "
                    "asignación compuesta."
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


    def _analyze_array_assignment(
        self,
        node,
        env,
        value_type
    ):
        """Analiza array[indice] = valor."""

        target = node.target

        # Valida arreglo, índice y bounds.
        element_type = self._infer_array_access(
            target,
            env
        )

        if element_type is None:
            return

        # -----------------------------------------------------
        # Encontrar la variable base
        # -----------------------------------------------------

        base_identifier = self._base_identifier(
            target.arreglo
        )

        if base_identifier is None:
            return

        symbol = env.lookup(
            base_identifier.nombre
        )

        if symbol is None:
            return

        # -----------------------------------------------------
        # El arreglo debe ser mutable
        # -----------------------------------------------------

        if not symbol.mutable:
            self._semantic_error(
                target,
                (
                    f"No es posible modificar la variable "
                    f"'{symbol.nombre}' porque fue declarada "
                    f"como inmutable."
                )
            )

            return

        # -----------------------------------------------------
        # Tipo del nuevo elemento
        # -----------------------------------------------------

        if not self._types_compatible(
            element_type,
            value_type
        ):
            self._semantic_error(
                node,
                (
                    f"No es posible asignar un valor de tipo "
                    f"{self._type_to_string(value_type)} "
                    f"a un elemento de tipo "
                    f"{self._type_to_string(element_type)}."
                )
            )


    def _base_identifier(self, expression):
        """Obtiene la variable base de un acceso anidado."""

        actual = expression

        while isinstance(
            actual,
            (
                ArrayAccess,
                SliceAccess,
                FieldAccess,
            )
        ):
            if isinstance(actual, FieldAccess):
                actual = actual.objeto
            else:
                actual = actual.arreglo

        if isinstance(actual, Identifier):
            return actual

        return None


    def _analyze_array_compound_assignment(
        self,
        node,
        env
    ):
        """Analiza array[i] += valor, etc."""

        target_type = self._infer_array_access(
            node.target,
            env
        )

        value_type = self._infer_type(
            node.valor,
            env
        )

        if target_type is None or value_type is None:
            return

        base_identifier = self._base_identifier(
            node.target.arreglo
        )

        if base_identifier is None:
            return

        symbol = env.lookup(
            base_identifier.nombre
        )

        if symbol is None:
            return

        if not symbol.mutable:
            self._semantic_error(
                node.target,
                (
                    f"No es posible modificar la variable "
                    f"'{symbol.nombre}' porque fue declarada "
                    f"como inmutable."
                )
            )

            return

        operators = {
            '+=': '+',
            '-=': '-',
            '*=': '*',
            '/=': '/',
            '%=': '%',
        }

        operator = operators.get(
            node.op
        )

        if operator is None:
            return

        operation = BinaryOp(
            node.target,
            operator,
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
            target_type,
            result_type
        ):
            self._semantic_error(
                node,
                (
                    f"El resultado de '{node.op}' es de tipo "
                    f"{self._type_to_string(result_type)} "
                    f"y no puede almacenarse en un elemento "
                    f"de tipo {self._type_to_string(target_type)}."
                )
            )


    def _analyze_field_assignment(
        self,
        node,
        env,
        value_type
    ):
        """Analiza objeto.campo = valor."""

        field_type = self._infer_field_access(
            node.target,
            env
        )

        if field_type is None:
            return

        base_identifier = self._base_identifier(
            node.target
        )

        if base_identifier is None:
            return

        symbol = env.lookup(
            base_identifier.nombre
        )

        if symbol is None:
            return

        if not symbol.mutable:
            self._semantic_error(
                node.target,
                (
                    f"No es posible modificar la variable "
                    f"'{symbol.nombre}' porque fue declarada "
                    "como inmutable."
                )
            )
            return

        if not self._types_compatible(
            field_type,
            value_type
        ):
            self._semantic_error(
                node,
                (
                    f"No es posible asignar un valor de tipo "
                    f"{self._type_to_string(value_type)} "
                    f"a un campo de tipo "
                    f"{self._type_to_string(field_type)}."
                )
            )


    def _analyze_field_compound_assignment(
        self,
        node,
        env
    ):
        """Analiza objeto.campo += valor, etc."""

        target_type = self._infer_field_access(
            node.target,
            env
        )

        value_type = self._infer_type(
            node.valor,
            env
        )

        if target_type is None or value_type is None:
            return

        base_identifier = self._base_identifier(
            node.target
        )

        if base_identifier is None:
            return

        symbol = env.lookup(
            base_identifier.nombre
        )

        if symbol is None:
            return

        if not symbol.mutable:
            self._semantic_error(
                node.target,
                (
                    f"No es posible modificar la variable "
                    f"'{symbol.nombre}' porque fue declarada "
                    "como inmutable."
                )
            )
            return

        operators = {
            '+=': '+',
            '-=': '-',
            '*=': '*',
            '/=': '/',
            '%=': '%',
        }

        operator = operators.get(node.op)

        if operator is None:
            return

        operation = BinaryOp(
            node.target,
            operator,
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
            target_type,
            result_type
        ):
            self._semantic_error(
                node,
                (
                    f"El resultado de '{node.op}' es de tipo "
                    f"{self._type_to_string(result_type)} "
                    f"y no puede almacenarse en un campo "
                    f"de tipo {self._type_to_string(target_type)}."
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

        if isinstance(expression, StructInit):
            return self._infer_struct_init(
                expression,
                env
            )

        if isinstance(expression, FieldAccess):
            return self._infer_field_access(
                expression,
                env
            )

        if isinstance(expression, MethodCall):
            return self._infer_method_call(
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

            if symbol.categoria not in (
                'variable',
                'parametro',
            ):
                self._semantic_error(
                    expression,
                    (
                        f"El identificador '{expression.nombre}' "
                        "no representa un valor utilizable en esta expresión."
                    )
                )
                return None

            if not getattr(symbol, 'inicializado', True):
                self._semantic_error(
                    expression,
                    (
                        f"La variable '{expression.nombre}' "
                        "no ha sido inicializada."
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

        if isinstance(expression, ArrayLiteral):
            return self._infer_array_literal(
                expression,
                env
            )

        if isinstance(expression, ArrayRepeat):
            return self._infer_array_repeat(
                expression,
                env
            )

        if isinstance(expression, ArrayAccess):
            return self._infer_array_access(
                expression,
                env
            )

        if isinstance(expression, SliceAccess):
            return self._infer_slice_access(
                expression,
                env
            )
        
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

        if expression.nombre in (
            'typeof',
            'random',
        ):
            return self._infer_builtin_function(
                expression,
                env
            )

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


    def _infer_struct_init(self, expression, env):
        """Valida la creación de una instancia de struct."""

        symbol = self.global_env.lookup_local(
            expression.nombre
        )

        if (
            symbol is None
            or symbol.categoria != 'struct'
        ):
            self._semantic_error(
                expression,
                (
                    f"El struct '{expression.nombre}' "
                    "no ha sido declarado."
                )
            )

            for _, value in expression.campos:
                self._infer_type(value, env)

            return None

        struct_decl = symbol.valor

        expected_fields = {
            field.nombre: field
            for field in struct_decl.campos
        }

        received_names = set()

        for field_name, value in expression.campos:
            value_type = self._infer_type(
                value,
                env
            )

            if field_name in received_names:
                self._semantic_error(
                    expression,
                    (
                        f"El campo '{field_name}' fue "
                        f"inicializado más de una vez en "
                        f"'{expression.nombre}'."
                    )
                )
                continue

            received_names.add(field_name)

            expected_field = expected_fields.get(
                field_name
            )

            if expected_field is None:
                self._semantic_error(
                    expression,
                    (
                        f"El struct '{expression.nombre}' "
                        f"no contiene un campo llamado "
                        f"'{field_name}'."
                    )
                )
                continue

            if (
                value_type is not None
                and not self._types_compatible(
                    expected_field.tipo,
                    value_type
                )
            ):
                self._semantic_error(
                    expression,
                    (
                        f"El campo '{field_name}' de "
                        f"'{expression.nombre}' esperaba "
                        f"{self._type_to_string(expected_field.tipo)}, "
                        f"pero recibió "
                        f"{self._type_to_string(value_type)}."
                    )
                )

        for field_name in expected_fields:
            if field_name not in received_names:
                self._semantic_error(
                    expression,
                    (
                        f"Falta inicializar el campo "
                        f"'{field_name}' del struct "
                        f"'{expression.nombre}'."
                    )
                )

        return expression.nombre


    def _infer_field_access(self, expression, env):
        """Valida objeto.campo y devuelve el tipo del campo."""

        object_type = self._infer_type(
            expression.objeto,
            env
        )

        if object_type is None:
            return None

        struct_symbol = self.global_env.lookup_local(
            object_type
        )

        if (
            struct_symbol is None
            or struct_symbol.categoria != 'struct'
        ):
            self._semantic_error(
                expression,
                (
                    f"El tipo "
                    f"'{self._type_to_string(object_type)}' "
                    "no posee campos."
                )
            )
            return None

        struct_decl = struct_symbol.valor

        for field in struct_decl.campos:
            if field.nombre == expression.campo:
                return field.tipo

        self._semantic_error(
            expression,
            (
                f"El struct '{struct_decl.nombre}' "
                f"no contiene un campo llamado "
                f"'{expression.campo}'."
            )
        )

        return None


    def _infer_builtin_function(self, expression, env):
        """Valida funciones globales embebidas."""

        name = expression.nombre

        argument_types = [
            self._infer_type(argument, env)
            for argument in expression.argumentos
        ]

        if name == 'typeof':
            if len(argument_types) != 1:
                self._semantic_error(
                    expression,
                    (
                        "La función 'typeof' esperaba "
                        f"1 argumento, pero recibió "
                        f"{len(argument_types)}."
                    )
                )

            return 'String'

        if name == 'random':
            if len(argument_types) != 2:
                self._semantic_error(
                    expression,
                    (
                        "La función 'random' esperaba "
                        f"2 argumentos, pero recibió "
                        f"{len(argument_types)}."
                    )
                )
                return None

            left_type = argument_types[0]
            right_type = argument_types[1]

            if left_type is None or right_type is None:
                return None

            numeric = {
                'i32',
                'f64',
            }

            if (
                left_type not in numeric
                or right_type not in numeric
            ):
                self._semantic_error(
                    expression,
                    (
                        "La función 'random' requiere "
                        "argumentos numéricos."
                    )
                )
                return None

            if (
                left_type == 'f64'
                or right_type == 'f64'
            ):
                return 'f64'

            return 'i32'

        return None


    def _infer_method_call(self, expression, env):
        """Valida métodos embebidos de String y Array."""

        object_type = self._infer_type(
            expression.objeto,
            env
        )

        argument_types = [
            self._infer_type(argument, env)
            for argument in expression.argumentos
        ]

        if object_type is None:
            return None

        method = expression.metodo

        # =====================================================
        # STRING
        # =====================================================

        if object_type == 'String':

            if method == 'len':
                if not self._method_arity(expression, 0):
                    return None
                return 'i32'

            if method == 'contains':
                if not self._method_arity(expression, 1):
                    return None

                if (
                    argument_types[0] is not None
                    and argument_types[0] != 'String'
                ):
                    self._semantic_error(
                        expression,
                        (
                            "String.contains() esperaba "
                            "un argumento de tipo String."
                        )
                    )
                    return None

                return 'bool'

            if method == 'replace':
                if not self._method_arity(expression, 2):
                    return None

                for arg_type in argument_types:
                    if (
                        arg_type is not None
                        and arg_type != 'String'
                    ):
                        self._semantic_error(
                            expression,
                            (
                                "String.replace() requiere "
                                "dos argumentos String."
                            )
                        )
                        return None

                return 'String'

            if method == 'split':
                if not self._method_arity(expression, 1):
                    return None

                if (
                    argument_types[0] is not None
                    and argument_types[0] != 'String'
                ):
                    self._semantic_error(
                        expression,
                        (
                            "String.split() esperaba "
                            "un separador de tipo String."
                        )
                    )
                    return None

                return (
                    'array',
                    'String',
                    None
                )

            if method in (
                'to_uppercase',
                'to_lowercase',
            ):
                if not self._method_arity(expression, 0):
                    return None

                return 'String'

        # =====================================================
        # ARRAY
        # =====================================================

        if (
            isinstance(object_type, tuple)
            and len(object_type) == 3
            and object_type[0] == 'array'
        ):
            element_type = object_type[1]

            if method == 'len':
                if not self._method_arity(expression, 0):
                    return None
                return 'i32'

            if method == 'contains':
                if not self._method_arity(expression, 1):
                    return None

                actual_type = argument_types[0]

                if (
                    element_type is not None
                    and actual_type is not None
                    and not self._types_compatible(
                        element_type,
                        actual_type
                    )
                ):
                    self._semantic_error(
                        expression,
                        (
                            "Array.contains() recibió un valor "
                            f"de tipo "
                            f"{self._type_to_string(actual_type)}, "
                            f"pero los elementos son "
                            f"{self._type_to_string(element_type)}."
                        )
                    )
                    return None

                return 'bool'

            if method == 'reverse':
                if not self._method_arity(expression, 0):
                    return None

                base_identifier = self._base_identifier(
                    expression.objeto
                )

                if base_identifier is None:
                    self._semantic_error(
                        expression,
                        (
                            "reverse() requiere un arreglo "
                            "mutable almacenado en una variable."
                        )
                    )
                    return None

                symbol = env.lookup(
                    base_identifier.nombre
                )

                if symbol is None:
                    return None

                if not symbol.mutable:
                    self._semantic_error(
                        expression,
                        (
                            f"No es posible modificar la variable "
                            f"'{symbol.nombre}' porque fue declarada "
                            "como inmutable."
                        )
                    )
                    return None

                return None

        self._semantic_error(
            expression,
            (
                f"El método '{method}' no está definido "
                f"para el tipo "
                f"{self._type_to_string(object_type)}."
            )
        )

        return None


    def _method_arity(self, expression, expected):
        """Valida número de argumentos de un método."""

        received = len(expression.argumentos)

        if received == expected:
            return True

        self._semantic_error(
            expression,
            (
                f"El método '{expression.metodo}' "
                f"esperaba {expected} argumentos, "
                f"pero recibió {received}."
            )
        )

        return False


    def _infer_array_literal(self, expression, env):
        """Infiere el tipo de un literal de arreglo."""

        elementos = expression.elementos

        # []
        if len(elementos) == 0:
            return (
                'array',
                None,
                0
            )

        tipos = []

        for elemento in elementos:
            tipo = self._infer_type(
                elemento,
                env
            )

            tipos.append(tipo)

        # Evitar cascadas si alguno ya produjo error.
        tipos_conocidos = [
            tipo
            for tipo in tipos
            if tipo is not None
        ]

        if not tipos_conocidos:
            return (
                'array',
                None,
                len(elementos)
            )

        tipo_base = tipos_conocidos[0]

        for tipo in tipos_conocidos[1:]:

            if not self._types_compatible(
                tipo_base,
                tipo
            ):
                self._semantic_error(
                    expression,
                    (
                        'Todos los elementos de un arreglo '
                        'deben ser del mismo tipo. '
                        f'Se encontraron '
                        f'{self._type_to_string(tipo_base)} '
                        f'y {self._type_to_string(tipo)}.'
                    )
                )

                return None

        return (
            'array',
            tipo_base,
            len(elementos)
        )


    def _infer_array_repeat(self, expression, env):
        """Infiere el tipo de [valor; cantidad]."""

        element_type = self._infer_type(
            expression.valor,
            env
        )

        if element_type is None:
            return None

        return (
            'array',
            element_type,
            expression.cantidad
        )

    def _infer_array_access(self, expression, env):
        """Valida array[indice] y devuelve el tipo del elemento."""

        array_type = self._infer_type(
            expression.arreglo,
            env
        )

        index_type = self._infer_type(
            expression.indice,
            env
        )

        if array_type is None or index_type is None:
            return None

        # -----------------------------------------------------
        # El índice debe ser i32
        # -----------------------------------------------------

        if index_type != 'i32':
            self._semantic_error(
                expression.indice,
                (
                    'El índice de un arreglo debe ser de tipo '
                    f'i32, no {self._type_to_string(index_type)}.'
                )
            )

            return None

        # -----------------------------------------------------
        # Debe tratarse de un arreglo
        # -----------------------------------------------------

        if not (
            isinstance(array_type, tuple)
            and len(array_type) == 3
            and array_type[0] == 'array'
        ):
            self._semantic_error(
                expression,
                (
                    'Solo es posible utilizar acceso por índice '
                    'sobre un arreglo.'
                )
            )

            return None

        element_type = array_type[1]
        length = array_type[2]

        # -----------------------------------------------------
        # Bounds estáticos
        # -----------------------------------------------------

        constant_index = self._constant_int(
            expression.indice
        )

        if (
            length is not None
            and constant_index is not None
        ):

            if (
                constant_index < 0
                or constant_index >= length
            ):
                self._semantic_error(
                    expression,
                    'Índice fuera de los límites del arreglo.'
                )

                return None

        return element_type


    def _infer_slice_access(self, expression, env):
        """Valida &array[inicio..fin]."""

        array_type = self._infer_type(
            expression.arreglo,
            env
        )

        start_type = self._infer_type(
            expression.inicio,
            env
        )

        end_type = self._infer_type(
            expression.fin,
            env
        )

        if (
            array_type is None
            or start_type is None
            or end_type is None
        ):
            return None

        # -----------------------------------------------------
        # Debe ser arreglo
        # -----------------------------------------------------

        if not (
            isinstance(array_type, tuple)
            and len(array_type) == 3
            and array_type[0] == 'array'
        ):
            self._semantic_error(
                expression,
                'Solo es posible crear un slice a partir de un arreglo.'
            )

            return None

        # -----------------------------------------------------
        # Índices i32
        # -----------------------------------------------------

        if start_type != 'i32':
            self._semantic_error(
                expression.inicio,
                (
                    'El índice inicial de un slice debe ser '
                    f'i32, no {self._type_to_string(start_type)}.'
                )
            )

            return None

        if end_type != 'i32':
            self._semantic_error(
                expression.fin,
                (
                    'El índice final de un slice debe ser '
                    f'i32, no {self._type_to_string(end_type)}.'
                )
            )

            return None

        length = array_type[2]

        start = self._constant_int(
            expression.inicio
        )

        end = self._constant_int(
            expression.fin
        )

        # -----------------------------------------------------
        # Bounds conocidos en compilación
        # -----------------------------------------------------

        if (
            length is not None
            and start is not None
            and end is not None
        ):

            if (
                start < 0
                or end < 0
                or start > end
                or start > length
                or end > length
            ):
                self._semantic_error(
                    expression,
                    'Rango fuera de los límites del arreglo.'
                )

                return None

        return (
            'slice',
            array_type[1]
        )


    
    def _constant_int(self, expression):
        """
        Obtiene un entero constante cuando puede determinarse
        durante el análisis semántico.
        """

        if (
            isinstance(expression, Literal)
            and expression.tipo == 'i32'
        ):
            return expression.valor

        if (
            isinstance(expression, UnaryOp)
            and expression.op == '-'
            and isinstance(expression.operando, Literal)
            and expression.operando.tipo == 'i32'
        ):
            return -expression.operando.valor

        return None

    
    # =========================================================
    # UTILIDADES DE TIPOS
    # =========================================================


    def _type_to_string(self, tipo):
        if tipo is None:
            return 'desconocido'

        if isinstance(tipo, tuple):

            if (
                len(tipo) == 3
                and tipo[0] == 'array'
            ):
                if tipo[2] is None:
                    return (
                        f'[{self._type_to_string(tipo[1])}]'
                    )

                return (
                    f'[{self._type_to_string(tipo[1])}; '
                    f'{tipo[2]}]'
                )

            if (
                len(tipo) == 2
                and tipo[0] == 'slice'
            ):
                return (
                    f'&[{self._type_to_string(tipo[1])}]'
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