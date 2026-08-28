import json
import math
import random
import re

from interpreter.ast.nodes import (
    Program,
    FunctionDecl,
    StructDecl,
    VarDeclaration,
    Assignment,
    CompoundAssignment,
    IfStmt,
    WhileStmt,
    LoopStmt,
    MatchStmt,
    Block,
    ReturnStmt,
    BreakStmt,
    ContinueStmt,
    ExpressionStmt,
    Literal,
    Identifier,
    BinaryOp,
    UnaryOp,
    Comparison,
    LogicalOp,
    ArrayLiteral,
    ArrayRepeat,
    ArrayAccess,
    SliceAccess,
    FieldAccess,
    FunctionCall,
    MethodCall,
    StringFrom,
    StringNew,
    PrintlnCall,
    StructInit,
)
from interpreter.errors import ErrorList
from interpreter.runtime.environment import RuntimeEnvironment
from interpreter.runtime.signals import (
    ReturnSignal,
    BreakSignal,
    ContinueSignal,
)
from interpreter.runtime.value import RuntimeValue


class Interpreter:
    """
    Intérprete del AST de OxigenScript.

    Esta clase asume que el AST ya pasó análisis léxico, sintáctico
    y semántico. Aun así, conserva validaciones dinámicas necesarias
    como división entre cero e índices calculados en tiempo de ejecución.
    """

    def __init__(self, errors=None, source_code=''):
        if errors is None:
            errors = ErrorList()

        self.errors = errors
        self.source_code = source_code
        self.source_lines = source_code.splitlines()

        self.functions = {}
        self.structs = {}

        self.global_env = RuntimeEnvironment('global')
        self.output_lines = []
        self.scope_counter = 0

    # =========================================================
    # API PRINCIPAL
    # =========================================================

    def execute(self, ast):
        if ast is None:
            return ''

        if not isinstance(ast, Program):
            raise TypeError('Interpreter esperaba un nodo Program.')

        self._register_globals(ast)

        main = self.functions.get('main')

        if main is None:
            self._error(
                ast,
                "El programa debe definir una función 'main'."
            )
            return self.output

        self._call_user_function(
            main,
            [],
        )

        return self.output

    @property
    def output(self):
        return '\n'.join(self.output_lines)

    # =========================================================
    # REGISTRO GLOBAL
    # =========================================================

    def _register_globals(self, program):
        for declaration in program.declaraciones:
            if isinstance(declaration, FunctionDecl):
                self.functions[declaration.nombre] = declaration

            elif isinstance(declaration, StructDecl):
                self.structs[declaration.nombre] = declaration

    # =========================================================
    # FUNCIONES
    # =========================================================

    def _call_user_function(self, function, arguments):
        env = self.global_env.create_child(
            f'fn::{function.nombre}'
        )

        for param, argument in zip(function.params, arguments):
            env.define(
                param.nombre,
                argument.clone(),
                mutable=False,
                initialized=True,
            )

        try:
            self._execute_block(
                function.cuerpo,
                env,
                create_scope=False,
            )

        except ReturnSignal as signal:
            return signal.value

        return RuntimeValue(
            None,
            function.tipo_retorno,
        )

    # =========================================================
    # BLOQUES E INSTRUCCIONES
    # =========================================================

    def _new_scope(self, env, kind):
        self.scope_counter += 1
        return env.create_child(
            f'{env.nombre}::{kind}_{self.scope_counter}'
        )

    def _execute_block(self, block, env, create_scope=True):
        if create_scope:
            env = self._new_scope(
                env,
                'block',
            )

        for instruction in block.instrucciones:
            self._execute_instruction(
                instruction,
                env,
            )

    def _execute_instruction(self, instruction, env):
        if isinstance(instruction, VarDeclaration):
            self._execute_var_declaration(
                instruction,
                env,
            )
            return

        if isinstance(instruction, Assignment):
            value = self._eval(
                instruction.valor,
                env,
            )
            self._assign_target(
                instruction.target,
                value,
                env,
                instruction,
            )
            return

        if isinstance(instruction, CompoundAssignment):
            self._execute_compound_assignment(
                instruction,
                env,
            )
            return

        if isinstance(instruction, Block):
            self._execute_block(
                instruction,
                env,
                create_scope=True,
            )
            return

        if isinstance(instruction, IfStmt):
            self._execute_if(
                instruction,
                env,
            )
            return

        if isinstance(instruction, WhileStmt):
            self._execute_while(
                instruction,
                env,
            )
            return

        if isinstance(instruction, LoopStmt):
            self._execute_loop(
                instruction,
                env,
            )
            return

        if isinstance(instruction, MatchStmt):
            self._execute_match(
                instruction,
                env,
            )
            return

        if isinstance(instruction, ReturnStmt):
            if instruction.valor is None:
                value = RuntimeValue(
                    None,
                    None,
                )
            else:
                value = self._eval(
                    instruction.valor,
                    env,
                )

            raise ReturnSignal(
                value
            )

        if isinstance(instruction, BreakStmt):
            raise BreakSignal(
                instruction.etiqueta
            )

        if isinstance(instruction, ContinueStmt):
            raise ContinueSignal(
                instruction.etiqueta
            )

        if isinstance(instruction, ExpressionStmt):
            self._eval(
                instruction.expresion,
                env,
            )
            return

    def _execute_var_declaration(self, node, env):
        if node.valor is not None:
            value = self._eval(
                node.valor,
                env,
            )

            env.define(
                node.nombre,
                value,
                mutable=node.mutable,
                initialized=True,
            )
            return

        default = self._default_value(
            node.tipo
        )

        if default is not None:
            env.define(
                node.nombre,
                default,
                mutable=node.mutable,
                initialized=True,
            )
            return

        env.define(
            node.nombre,
            RuntimeValue(
                None,
                node.tipo,
            ),
            mutable=node.mutable,
            initialized=False,
        )

    def _execute_compound_assignment(self, node, env):
        current = self._eval(
            node.target,
            env,
        )

        right = self._eval(
            node.valor,
            env,
        )

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
            self._error(
                node,
                f"Operador compuesto desconocido '{node.op}'."
            )
            return

        result = self._binary_values(
            current,
            operator,
            right,
            node,
        )

        self._assign_target(
            node.target,
            result,
            env,
            node,
        )

    # =========================================================
    # CONTROL DE FLUJO
    # =========================================================

    def _execute_if(self, node, env):
        condition = self._eval(
            node.condicion,
            env,
        )

        if bool(condition.value):
            self._execute_block(
                node.cuerpo,
                env,
                create_scope=True,
            )
            return

        if node.else_branch is None:
            return

        if isinstance(node.else_branch, IfStmt):
            self._execute_if(
                node.else_branch,
                env,
            )
            return

        self._execute_block(
            node.else_branch,
            env,
            create_scope=True,
        )

    def _execute_while(self, node, env):
        while True:
            condition = self._eval(
                node.condicion,
                env,
            )

            if not bool(condition.value):
                break

            try:
                self._execute_block(
                    node.cuerpo,
                    env,
                    create_scope=True,
                )

            except ContinueSignal as signal:
                # Un while no posee label propio. Un continue etiquetado
                # debe propagarse hacia el loop etiquetado exterior.
                if signal.label is None:
                    continue

                raise

            except BreakSignal as signal:
                if signal.label is None:
                    break

                raise

    def _execute_loop(self, node, env):
        while True:
            try:
                self._execute_block(
                    node.cuerpo,
                    env,
                    create_scope=True,
                )

            except ContinueSignal as signal:
                if (
                    signal.label is None
                    or signal.label == node.etiqueta
                ):
                    continue

                raise

            except BreakSignal as signal:
                if (
                    signal.label is None
                    or signal.label == node.etiqueta
                ):
                    break

                raise

    def _execute_match(self, node, env):
        target = self._eval(
            node.expresion,
            env,
        )

        for arm in node.brazos:
            arm_env = self._new_scope(
                env,
                'match',
            )

            if not self._match_arm(
                arm.patron,
                target,
                env,
                arm_env,
            ):
                continue

            if isinstance(arm.cuerpo, Block):
                self._execute_block(
                    arm.cuerpo,
                    arm_env,
                    create_scope=False,
                )
            else:
                self._eval(
                    arm.cuerpo,
                    arm_env,
                )

            return

    def _match_arm(self, pattern, target, env, arm_env):
        if isinstance(pattern, Identifier):
            if pattern.nombre == '_':
                return True

            # Un identificador en un patrón funciona como binding.
            arm_env.define(
                pattern.nombre,
                target.clone(),
                mutable=False,
                initialized=True,
            )
            return True

        pattern_value = self._eval(
            pattern,
            env,
        )

        return self._values_equal(
            pattern_value,
            target,
        )

    # =========================================================
    # EVALUACIÓN DE EXPRESIONES
    # =========================================================

    def _eval(self, expression, env):
        if expression is None:
            return RuntimeValue()

        if isinstance(expression, Literal):
            tipo = getattr(
                expression,
                'tipo',
                None,
            )

            if tipo is None:
                tipo = self._infer_python_literal_type(
                    expression.valor
                )

            return RuntimeValue(
                expression.valor,
                tipo,
            )

        if isinstance(expression, Identifier):
            variable = env.lookup(
                expression.nombre
            )

            if variable is None:
                self._error(
                    expression,
                    f"La variable '{expression.nombre}' no ha sido declarada."
                )
                return RuntimeValue()

            if not variable.initialized:
                self._error(
                    expression,
                    (
                        f"La variable '{expression.nombre}' "
                        "no ha sido inicializada."
                    )
                )
                return RuntimeValue()

            return variable.valor

        if isinstance(expression, BinaryOp):
            left = self._eval(
                expression.izq,
                env,
            )

            right = self._eval(
                expression.der,
                env,
            )

            return self._binary_values(
                left,
                expression.op,
                right,
                expression,
            )

        if isinstance(expression, UnaryOp):
            return self._eval_unary(
                expression,
                env,
            )

        if isinstance(expression, Comparison):
            return self._eval_comparison(
                expression,
                env,
            )

        if isinstance(expression, LogicalOp):
            return self._eval_logical(
                expression,
                env,
            )

        if isinstance(expression, ArrayLiteral):
            elements = [
                self._eval(
                    element,
                    env,
                )
                for element in expression.elementos
            ]

            element_type = (
                elements[0].tipo
                if elements
                else None
            )

            return RuntimeValue(
                elements,
                (
                    'array',
                    element_type,
                    len(elements),
                ),
            )

        if isinstance(expression, ArrayRepeat):
            value = self._eval(
                expression.valor,
                env,
            )

            elements = [
                value.clone()
                for _ in range(expression.cantidad)
            ]

            return RuntimeValue(
                elements,
                (
                    'array',
                    value.tipo,
                    expression.cantidad,
                ),
            )

        if isinstance(expression, ArrayAccess):
            array = self._eval(
                expression.arreglo,
                env,
            )

            index = self._eval(
                expression.indice,
                env,
            )

            return self._array_access(
                expression,
                array,
                index,
            )

        if isinstance(expression, SliceAccess):
            array = self._eval(
                expression.arreglo,
                env,
            )

            start = self._eval(
                expression.inicio,
                env,
            )

            end = self._eval(
                expression.fin,
                env,
            )

            return self._slice_access(
                expression,
                array,
                start,
                end,
            )

        if isinstance(expression, FieldAccess):
            obj = self._eval(
                expression.objeto,
                env,
            )

            if not isinstance(obj.value, dict):
                self._error(
                    expression,
                    (
                        f"El tipo {self._type_to_string(obj.tipo)} "
                        "no posee campos."
                    )
                )
                return RuntimeValue()

            value = obj.value.get(
                expression.campo
            )

            if value is None:
                self._error(
                    expression,
                    (
                        f"El struct '{self._type_to_string(obj.tipo)}' "
                        f"no contiene el campo '{expression.campo}'."
                    )
                )
                return RuntimeValue()

            return value

        if isinstance(expression, FunctionCall):
            return self._eval_function_call(
                expression,
                env,
            )

        if isinstance(expression, MethodCall):
            return self._eval_method_call(
                expression,
                env,
            )

        if isinstance(expression, StringFrom):
            argument = self._eval(
                expression.argumento,
                env,
            )

            return RuntimeValue(
                str(argument.value),
                'String',
            )

        if isinstance(expression, StringNew):
            return RuntimeValue(
                '',
                'String',
            )

        if isinstance(expression, PrintlnCall):
            return self._eval_println(
                expression,
                env,
            )

        if isinstance(expression, StructInit):
            fields = {}

            for name, value_expression in expression.campos:
                fields[name] = self._eval(
                    value_expression,
                    env,
                )

            return RuntimeValue(
                fields,
                expression.nombre,
            )

        self._error(
            expression,
            (
                f"No existe ejecución definida para "
                f"{type(expression).__name__}."
            )
        )
        return RuntimeValue()

    # =========================================================
    # OPERADORES
    # =========================================================

    def _binary_values(self, left, operator, right, node):
        if operator == '+':
            if left.tipo == 'String' and right.tipo == 'String':
                return RuntimeValue(
                    str(left.value) + str(right.value),
                    'String',
                )

        if operator == '*':
            if left.tipo == 'String' and right.tipo == 'i32':
                return RuntimeValue(
                    str(left.value) * int(right.value),
                    'String',
                )

            if left.tipo == 'i32' and right.tipo == 'String':
                return RuntimeValue(
                    str(right.value) * int(left.value),
                    'String',
                )

        numeric = {
            'i32',
            'f64',
        }

        if (
            left.tipo not in numeric
            or right.tipo not in numeric
        ):
            self._error(
                node,
                (
                    f"No es posible aplicar el operador '{operator}' "
                    f"entre los tipos "
                    f"{self._type_to_string(left.tipo)} y "
                    f"{self._type_to_string(right.tipo)}."
                )
            )
            return RuntimeValue()

        result_type = (
            'f64'
            if 'f64' in (left.tipo, right.tipo)
            else 'i32'
        )

        a = left.value
        b = right.value

        try:
            if operator == '+':
                result = a + b

            elif operator == '-':
                result = a - b

            elif operator == '*':
                result = a * b

            elif operator == '/':
                if b == 0:
                    self._error(
                        node,
                        'División entre cero.'
                    )
                    return RuntimeValue()

                if result_type == 'i32':
                    # División entera estilo Rust: truncamiento hacia cero.
                    result = int(a / b)
                else:
                    result = a / b

            elif operator == '%':
                if b == 0:
                    self._error(
                        node,
                        'Módulo entre cero.'
                    )
                    return RuntimeValue()

                if result_type == 'i32':
                    quotient = int(a / b)
                    result = a - (quotient * b)
                else:
                    result = math.fmod(a, b)

            else:
                self._error(
                    node,
                    f"Operador aritmético desconocido '{operator}'."
                )
                return RuntimeValue()

        except (TypeError, ValueError, OverflowError) as exc:
            self._error(
                node,
                f"Error al evaluar '{operator}': {exc}"
            )
            return RuntimeValue()

        if result_type == 'i32':
            result = int(result)
        else:
            result = float(result)

        return RuntimeValue(
            result,
            result_type,
        )

    def _eval_unary(self, expression, env):
        operand = self._eval(
            expression.operando,
            env,
        )

        if expression.op == '-':
            return RuntimeValue(
                -operand.value,
                operand.tipo,
            )

        if expression.op == '!':
            return RuntimeValue(
                not bool(operand.value),
                'bool',
            )

        self._error(
            expression,
            f"Operador unario desconocido '{expression.op}'."
        )
        return RuntimeValue()

    def _eval_comparison(self, expression, env):
        left = self._eval(
            expression.izq,
            env,
        )

        right = self._eval(
            expression.der,
            env,
        )

        a, b = self._comparison_operands(
            left,
            right,
        )

        operators = {
            '==': lambda: a == b,
            '!=': lambda: a != b,
            '>': lambda: a > b,
            '>=': lambda: a >= b,
            '<': lambda: a < b,
            '<=': lambda: a <= b,
        }

        action = operators.get(
            expression.op
        )

        if action is None:
            self._error(
                expression,
                (
                    f"Operador relacional desconocido "
                    f"'{expression.op}'."
                )
            )
            return RuntimeValue()

        try:
            result = action()

        except TypeError:
            self._error(
                expression,
                (
                    f"No es posible comparar "
                    f"{self._type_to_string(left.tipo)} con "
                    f"{self._type_to_string(right.tipo)}."
                )
            )
            return RuntimeValue()

        return RuntimeValue(
            bool(result),
            'bool',
        )

    def _comparison_operands(self, left, right):
        if left.tipo == 'char' and right.tipo == 'i32':
            return ord(left.value), right.value

        if left.tipo == 'i32' and right.tipo == 'char':
            return left.value, ord(right.value)

        return left.value, right.value

    def _eval_logical(self, expression, env):
        left = self._eval(
            expression.izq,
            env,
        )

        # Corto circuito obligatorio.
        if expression.op == '&&':
            if not bool(left.value):
                return RuntimeValue(
                    False,
                    'bool',
                )

            right = self._eval(
                expression.der,
                env,
            )

            return RuntimeValue(
                bool(right.value),
                'bool',
            )

        if expression.op == '||':
            if bool(left.value):
                return RuntimeValue(
                    True,
                    'bool',
                )

            right = self._eval(
                expression.der,
                env,
            )

            return RuntimeValue(
                bool(right.value),
                'bool',
            )

        self._error(
            expression,
            (
                f"Operador lógico desconocido "
                f"'{expression.op}'."
            )
        )
        return RuntimeValue()

    # =========================================================
    # ARREGLOS / SLICES / ASSIGNABLES
    # =========================================================

    def _array_access(self, node, array, index):
        if not isinstance(array.value, list):
            self._error(
                node,
                'El valor no es un arreglo.'
            )
            return RuntimeValue()

        i = int(index.value)

        if i < 0 or i >= len(array.value):
            self._error(
                node,
                'Índice fuera de los límites del arreglo.'
            )
            return RuntimeValue()

        return array.value[i]

    def _slice_access(self, node, array, start, end):
        if not isinstance(array.value, list):
            self._error(
                node,
                'Solo es posible crear un slice de un arreglo.'
            )
            return RuntimeValue()

        i = int(start.value)
        j = int(end.value)

        if (
            i < 0
            or j < 0
            or i > j
            or i > len(array.value)
            or j > len(array.value)
        ):
            self._error(
                node,
                'Rango fuera de los límites del arreglo.'
            )
            return RuntimeValue()

        element_type = self._array_element_type(
            array.tipo
        )

        return RuntimeValue(
            [
                element.clone()
                for element in array.value[i:j]
            ],
            (
                'slice',
                element_type,
            ),
        )

    def _assign_target(self, target, value, env, node):
        if isinstance(target, Identifier):
            variable = env.lookup(
                target.nombre
            )

            if variable is None:
                self._error(
                    node,
                    f"La variable '{target.nombre}' no ha sido declarada."
                )
                return

            if (
                variable.initialized
                and not variable.mutable
            ):
                self._error(
                    node,
                    (
                        f"No es posible modificar la variable "
                        f"'{target.nombre}' porque fue declarada "
                        "como inmutable."
                    )
                )
                return

            variable.valor = value
            variable.initialized = True
            return

        if isinstance(target, ArrayAccess):
            array = self._eval(
                target.arreglo,
                env,
            )

            index = self._eval(
                target.indice,
                env,
            )

            if not isinstance(array.value, list):
                self._error(
                    node,
                    'El target no es un arreglo.'
                )
                return

            i = int(index.value)

            if i < 0 or i >= len(array.value):
                self._error(
                    node,
                    'Índice fuera de los límites del arreglo.'
                )
                return

            array.value[i] = value
            return

        if isinstance(target, FieldAccess):
            obj = self._eval(
                target.objeto,
                env,
            )

            if not isinstance(obj.value, dict):
                self._error(
                    node,
                    'El target no es un struct.'
                )
                return

            obj.value[target.campo] = value
            return

        self._error(
            node,
            'Target de asignación no soportado.'
        )

    # =========================================================
    # LLAMADAS
    # =========================================================

    def _eval_function_call(self, expression, env):
        if expression.nombre == 'typeof':
            if len(expression.argumentos) != 1:
                self._error(
                    expression,
                    "typeof() requiere un argumento."
                )
                return RuntimeValue()

            value = self._eval(
                expression.argumentos[0],
                env,
            )

            return RuntimeValue(
                self._type_to_string(
                    value.tipo
                ),
                'String',
            )

        if expression.nombre == 'random':
            if len(expression.argumentos) != 2:
                self._error(
                    expression,
                    'random() requiere dos argumentos.'
                )
                return RuntimeValue()

            minimum = self._eval(
                expression.argumentos[0],
                env,
            )

            maximum = self._eval(
                expression.argumentos[1],
                env,
            )

            if (
                minimum.tipo == 'i32'
                and maximum.tipo == 'i32'
            ):
                return RuntimeValue(
                    random.randint(
                        int(minimum.value),
                        int(maximum.value),
                    ),
                    'i32',
                )

            return RuntimeValue(
                random.uniform(
                    float(minimum.value),
                    float(maximum.value),
                ),
                'f64',
            )

        function = self.functions.get(
            expression.nombre
        )

        if function is None:
            self._error(
                expression,
                (
                    f"La función '{expression.nombre}' "
                    "no ha sido declarada."
                )
            )
            return RuntimeValue()

        arguments = [
            self._eval(
                argument,
                env,
            )
            for argument in expression.argumentos
        ]

        return self._call_user_function(
            function,
            arguments,
        )

    def _eval_method_call(self, expression, env):
        obj = self._eval(
            expression.objeto,
            env,
        )

        arguments = [
            self._eval(
                argument,
                env,
            )
            for argument in expression.argumentos
        ]

        method = expression.metodo

        # ---------------- String ----------------

        if obj.tipo == 'String':
            if method == 'len':
                return RuntimeValue(
                    len(obj.value),
                    'i32',
                )

            if method == 'contains':
                return RuntimeValue(
                    arguments[0].value in obj.value,
                    'bool',
                )

            if method == 'replace':
                return RuntimeValue(
                    obj.value.replace(
                        str(arguments[0].value),
                        str(arguments[1].value),
                    ),
                    'String',
                )

            if method == 'split':
                separator = str(
                    arguments[0].value
                )

                if separator == '':
                    self._error(
                        expression,
                        'split() no acepta un separador vacío.'
                    )
                    return RuntimeValue()

                parts = obj.value.split(
                    separator
                )

                values = [
                    RuntimeValue(
                        part,
                        'String',
                    )
                    for part in parts
                ]

                return RuntimeValue(
                    values,
                    (
                        'array',
                        'String',
                        len(values),
                    ),
                )

            if method == 'to_uppercase':
                return RuntimeValue(
                    obj.value.upper(),
                    'String',
                )

            if method == 'to_lowercase':
                return RuntimeValue(
                    obj.value.lower(),
                    'String',
                )

        # ---------------- Array / Slice ----------------

        if self._is_array_like(
            obj.tipo
        ):
            if method == 'len':
                return RuntimeValue(
                    len(obj.value),
                    'i32',
                )

            if method == 'contains':
                needle = arguments[0]

                result = any(
                    self._values_equal(
                        item,
                        needle,
                    )
                    for item in obj.value
                )

                return RuntimeValue(
                    result,
                    'bool',
                )

            if method == 'reverse':
                obj.value.reverse()
                return RuntimeValue(
                    None,
                    None,
                )

        self._error(
            expression,
            (
                f"El método '{method}' no está definido "
                f"para el tipo {self._type_to_string(obj.tipo)}."
            )
        )
        return RuntimeValue()

    # =========================================================
    # PRINTLN
    # =========================================================

    def _eval_println(self, expression, env):
        values = [
            self._eval(
                argument,
                env,
            )
            for argument in expression.argumentos
        ]

        if not values:
            self.output_lines.append('')
            return RuntimeValue()

        first = values[0]

        if first.tipo == 'String':
            format_string = str(
                first.value
            )

            if len(values) == 1:
                self.output_lines.append(
                    format_string
                )
                return RuntimeValue()

            rendered = self._render_format_string(
                format_string,
                values[1:],
            )

            self.output_lines.append(
                rendered
            )
            return RuntimeValue()

        self.output_lines.append(
            ' '.join(
                self._format_normal(value)
                for value in values
            )
        )

        return RuntimeValue()

    def _render_format_string(self, format_string, values):
        pattern = re.compile(
            r'\{\:\?\}|\{\}'
        )

        index = 0

        def replacement(match):
            nonlocal index

            if index >= len(values):
                return match.group(0)

            value = values[index]
            index += 1

            if match.group(0) == '{:?}':
                return self._format_debug(
                    value
                )

            return self._format_normal(
                value
            )

        rendered = pattern.sub(
            replacement,
            format_string,
        )

        # Si sobran argumentos, no los descartamos silenciosamente.
        if index < len(values):
            extras = ' '.join(
                self._format_normal(value)
                for value in values[index:]
            )

            if extras:
                rendered = (
                    rendered
                    + (' ' if rendered else '')
                    + extras
                )

        return rendered

    def _format_normal(self, value):
        if value.tipo == 'bool':
            return (
                'true'
                if bool(value.value)
                else 'false'
            )

        if self._is_array_like(
            value.tipo
        ):
            return self._format_array(
                value.value,
                debug=False,
            )

        if isinstance(value.value, dict):
            return self._format_struct(
                value
            )

        if value.value is None:
            return ''

        return str(
            value.value
        )

    def _format_debug(self, value):
        if value.tipo == 'String':
            return json.dumps(
                str(value.value),
                ensure_ascii=False,
            )

        if value.tipo == 'char':
            return repr(
                value.value
            )

        if value.tipo == 'bool':
            return (
                'true'
                if bool(value.value)
                else 'false'
            )

        if self._is_array_like(
            value.tipo
        ):
            return self._format_array(
                value.value,
                debug=True,
            )

        if isinstance(value.value, dict):
            return self._format_struct(
                value
            )

        return str(
            value.value
        )

    def _format_array(self, elements, debug=False):
        formatter = (
            self._format_debug
            if debug
            else self._format_normal
        )

        return (
            '['
            + ', '.join(
                formatter(element)
                for element in elements
            )
            + ']'
        )

    def _format_struct(self, value):
        fields = ', '.join(
            (
                f'{name}: '
                f'{self._format_debug(field_value)}'
            )
            for name, field_value in value.value.items()
        )

        return (
            f'{self._type_to_string(value.tipo)} '
            f'{{ {fields} }}'
        )

    # =========================================================
    # HELPERS
    # =========================================================

    def _default_value(self, tipo):
        defaults = {
            'i32': RuntimeValue(0, 'i32'),
            'f64': RuntimeValue(0.0, 'f64'),
            'bool': RuntimeValue(False, 'bool'),
            'String': RuntimeValue('', 'String'),
        }

        value = defaults.get(
            tipo
        )

        if value is None:
            return None

        return value.clone()

    def _infer_python_literal_type(self, value):
        if isinstance(value, bool):
            return 'bool'

        if isinstance(value, int):
            return 'i32'

        if isinstance(value, float):
            return 'f64'

        if isinstance(value, str):
            return 'String'

        return None

    def _is_array_like(self, tipo):
        return (
            isinstance(tipo, tuple)
            and len(tipo) >= 2
            and tipo[0] in (
                'array',
                'slice',
            )
        )

    def _array_element_type(self, tipo):
        if self._is_array_like(
            tipo
        ):
            return tipo[1]

        return None

    def _type_to_string(self, tipo):
        if tipo is None:
            return 'None'

        if (
            isinstance(tipo, tuple)
            and len(tipo) == 3
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
            isinstance(tipo, tuple)
            and len(tipo) == 2
            and tipo[0] == 'slice'
        ):
            return (
                f'&[{self._type_to_string(tipo[1])}]'
            )

        return str(
            tipo
        )

    def _values_equal(self, left, right):
        if (
            self._is_array_like(left.tipo)
            and self._is_array_like(right.tipo)
        ):
            if len(left.value) != len(right.value):
                return False

            return all(
                self._values_equal(a, b)
                for a, b in zip(
                    left.value,
                    right.value,
                )
            )

        return left.value == right.value

    def _fragment(self, node):
        if not self.source_lines:
            return ''

        line = getattr(
            node,
            'linea',
            0,
        )

        if (
            line <= 0
            or line > len(self.source_lines)
        ):
            return ''

        return self.source_lines[
            line - 1
        ]

    def _error(self, node, description):
        self.errors.add(
            'Semántico',
            description,
            getattr(node, 'linea', 1),
            getattr(node, 'columna', 1),
            self._fragment(node),
        )
