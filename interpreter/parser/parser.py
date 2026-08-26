import ply.yacc as yacc

from interpreter.lexer.lexer import tokens, lexer as ox_lexer  # noqa: F401
from interpreter.errors import ErrorList
from interpreter.ast.nodes import (
    Program, FunctionDecl, Param, StructDecl, StructField,
    VarDeclaration, Assignment, CompoundAssignment,
    IfStmt, WhileStmt, LoopStmt, MatchStmt, MatchArm,
    Block, ReturnStmt, BreakStmt, ContinueStmt, ExpressionStmt,
    Literal, Identifier, BinaryOp, UnaryOp, Comparison, LogicalOp,
    ArrayLiteral, ArrayRepeat, ArrayAccess, SliceAccess, FieldAccess,
    FunctionCall, MethodCall, StringFrom, StringNew,
    PrintlnCall, StructInit,
)


# -------------------------------------------------------------------
# Precedencia (de menor a mayor)
# -------------------------------------------------------------------
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NEQ'),
    ('left', 'LT', 'LTE', 'GT', 'GTE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MODULO'),
    ('right', 'NOT', 'UMINUS'),
)

#-------------------------------------------------------------------
# Funciones auxiliares
#-------------------------------------------------------------------

def _pos(p, i):
    """Devuelve (linea, columna) del token i en la produccion."""
    linea = p.lineno(i)
    lexpos = p.lexpos(i)
    if lexpos is not None and lexpos >= 0:
        data = p.lexer.lexdata
        line_start = data.rfind('\n', 0, lexpos) + 1
        col = (lexpos - line_start) + 1
    else:
        col = 1
    return linea, col


def _es_target_asignable(nodo):
    """Indica si un nodo puede aparecer al lado izquierdo de una asignación."""
    return isinstance(
        nodo,
        (Identifier, FieldAccess, ArrayAccess)
    )


def _validar_condicion_if(condicion, p, indice_if):
    """Reporta error si toda la condición del if está entre paréntesis."""

    if getattr(condicion, '_parenthesized', False):
        linea, col = _pos(p, indice_if)

        p.lexer.errors.add(
            'Sintáctico',
            'No se permiten paréntesis alrededor de la condición del if',
            linea,
            col,
            _fragmento_desde_lexpos(
                p.lexer,
                p.lexpos(indice_if)
            )
        )


def _fragmento_desde_lexpos(lexer_obj, lexpos):
    """Obtiene la línea fuente correspondiente a una posición absoluta."""
    data = lexer_obj.lexdata

    line_start = data.rfind('\n', 0, lexpos) + 1
    line_end = data.find('\n', lexpos)

    if line_end == -1:
        line_end = len(data)

    return data[line_start:line_end]

def _posicion_eof(lexer_obj):
    """Obtiene línea, columna y fragmento útil cuando el error ocurre en EOF."""
    data = lexer_obj.lexdata

    if not data:
        return 1, 1, ''

    # Ignorar saltos de línea finales para apuntar
    # a la última línea real de código.
    pos = len(data.rstrip('\n'))

    line_start = data.rfind('\n', 0, pos) + 1

    line_end = data.find('\n', pos)
    if line_end == -1:
        line_end = len(data)

    linea = data.count('\n', 0, pos) + 1
    columna = (pos - line_start) + 1
    fragmento = data[line_start:line_end]

    return linea, columna, fragmento


# ===================================================================
# PROGRAMA
# ===================================================================

def p_programa(p):
    '''programa : declaraciones_globales'''
    p[0] = Program(p[1])


def p_declaraciones_lista(p):
    '''declaraciones_globales : declaraciones_globales declaracion_global'''
    p[0] = p[1] + [p[2]]


def p_declaraciones_vacio(p):
    '''declaraciones_globales : '''
    p[0] = []


def p_declaracion_funcion(p):
    '''declaracion_global : funcion_decl'''
    p[0] = p[1]


def p_declaracion_struct(p):
    '''declaracion_global : struct_decl'''
    p[0] = p[1]


# ===================================================================
# FUNCIONES
# ===================================================================

def p_funcion_con_retorno(p):
    '''funcion_decl : FN IDENTIFIER LPAREN parametros RPAREN ARROW tipo LBRACE instrucciones RBRACE'''
    linea, col = _pos(p, 1)
    cuerpo = Block(p[9], *_pos(p, 8))
    p[0] = FunctionDecl(p[2], p[4], p[7], cuerpo, linea, col)


def p_funcion_sin_retorno(p):
    '''funcion_decl : FN IDENTIFIER LPAREN parametros RPAREN LBRACE instrucciones RBRACE'''
    linea, col = _pos(p, 1)
    cuerpo = Block(p[7], *_pos(p, 6))
    p[0] = FunctionDecl(p[2], p[4], None, cuerpo, linea, col)


def p_parametros_lista(p):
    '''parametros : lista_params'''
    p[0] = p[1]


def p_parametros_vacio(p):
    '''parametros : '''
    p[0] = []


def p_lista_params_muchos(p):
    '''lista_params : lista_params COMMA param'''
    p[0] = p[1] + [p[3]]


def p_lista_params_uno(p):
    '''lista_params : param'''
    p[0] = [p[1]]


def p_param(p):
    '''param : IDENTIFIER COLON tipo'''
    p[0] = Param(p[1], p[3], *_pos(p, 1))


# ===================================================================
# TIPOS
# ===================================================================

def p_tipo_basico(p):
    '''tipo : I32
            | F64
            | BOOL
            | CHAR_TYPE
            | STRING_TYPE'''
    tipo_map = {
        'I32': 'i32', 'F64': 'f64', 'BOOL': 'bool',
        'CHAR_TYPE': 'char', 'STRING_TYPE': 'String',
    }
    p[0] = tipo_map.get(p.slice[1].type, p[1])


def p_tipo_struct(p):
    '''tipo : IDENTIFIER'''
    p[0] = p[1]


def p_tipo_arreglo(p):
    '''tipo : LBRACKET tipo SEMICOLON NUMBER_INT RBRACKET'''
    p[0] = ('array', p[2], p[4])


# ===================================================================
# STRUCTS
# ===================================================================

def p_struct_decl(p):
    '''struct_decl : STRUCT IDENTIFIER LBRACE campos_struct RBRACE'''
    p[0] = StructDecl(p[2], p[4], *_pos(p, 1))


def p_campos_struct_muchos(p):
    '''campos_struct : campo_struct COMMA campos_struct'''
    p[0] = [p[1]] + p[3]


def p_campos_struct_ultimo_coma(p):
    '''campos_struct : campo_struct COMMA'''
    p[0] = [p[1]]


def p_campos_struct_ultimo(p):
    '''campos_struct : campo_struct'''
    p[0] = [p[1]]


def p_campo_struct(p):
    '''campo_struct : IDENTIFIER COLON tipo'''
    p[0] = StructField(p[1], p[3], *_pos(p, 1))


# ===================================================================
# BLOQUE E INSTRUCCIONES
# ===================================================================

def p_instrucciones_lista(p):
    '''instrucciones : instrucciones instruccion'''

    if p[2] is None:
        p[0] = p[1]
    else:
        p[0] = p[1] + [p[2]]


def p_instrucciones_vacio(p):
    '''instrucciones : '''
    p[0] = []


def p_instruccion_let_falta_identificador(p):
    '''instruccion : LET EQUALS valor_init SEMICOLON
                   | LET MUT EQUALS valor_init SEMICOLON'''

    # Determinar dónde está el '=' según la alternativa.
    if len(p) == 5:
        # let = valor;
        indice_equals = 2
    else:
        # let mut = valor;
        indice_equals = 3

    linea = p.lineno(indice_equals)
    lexpos = p.lexpos(indice_equals)

    data = p.lexer.lexdata

    line_start = data.rfind('\n', 0, lexpos) + 1
    columna = (lexpos - line_start) + 1

    fragmento = _fragmento_desde_lexpos(
        p.lexer,
        lexpos
    )

    p.lexer.errors.add(
        'Sintáctico',
        'Se esperaba un identificador después de let',
        linea,
        columna,
        fragmento
    )

    # La instrucción inválida no se agrega al AST.
    p[0] = None


# --- Declaracion de variables ---

def p_instruccion_var_decl(p):
    '''instruccion : var_decl SEMICOLON'''
    p[0] = p[1]


def p_var_decl_tipo(p):
    '''var_decl : LET IDENTIFIER COLON tipo EQUALS valor_init'''
    p[0] = VarDeclaration(p[2], False, p[4], p[6], *_pos(p, 1))


def p_var_decl_sin_tipo(p):
    '''var_decl : LET IDENTIFIER EQUALS valor_init'''
    p[0] = VarDeclaration(p[2], False, None, p[4], *_pos(p, 1))


def p_var_decl_mut_tipo(p):
    '''var_decl : LET MUT IDENTIFIER COLON tipo EQUALS valor_init'''
    p[0] = VarDeclaration(p[3], True, p[5], p[7], *_pos(p, 1))


def p_var_decl_mut_sin_tipo(p):
    '''var_decl : LET MUT IDENTIFIER EQUALS valor_init'''
    p[0] = VarDeclaration(p[3], True, None, p[5], *_pos(p, 1))


def p_valor_init_expr(p):
    '''valor_init : expresion'''
    p[0] = p[1]


def p_valor_init_struct(p):
    '''valor_init : struct_init'''
    p[0] = p[1]

def p_var_decl_tipo_sin_valor(p):
    '''var_decl : LET IDENTIFIER COLON tipo'''
    p[0] = VarDeclaration(
        p[2],
        False,
        p[4],
        None,
        *_pos(p, 1)
    )


def p_var_decl_mut_tipo_sin_valor(p):
    '''var_decl : LET MUT IDENTIFIER COLON tipo'''
    p[0] = VarDeclaration(
        p[3],
        True,
        p[5],
        None,
        *_pos(p, 1)
    )


def p_var_decl_sin_tipo_sin_valor(p):
    '''var_decl : LET IDENTIFIER'''
    p[0] = VarDeclaration(
        p[2],
        False,
        None,
        None,
        *_pos(p, 1)
    )


def p_var_decl_mut_sin_tipo_sin_valor(p):
    '''var_decl : LET MUT IDENTIFIER'''
    p[0] = VarDeclaration(
        p[3],
        True,
        None,
        None,
        *_pos(p, 1)
    )

# --- Struct init (solo en contextos de asignacion/declaracion) ---

def p_struct_init(p):
    '''struct_init : IDENTIFIER LBRACE campo_inits RBRACE'''
    p[0] = StructInit(p[1], p[3], *_pos(p, 1))


def p_struct_init_vacio(p):
    '''struct_init : IDENTIFIER LBRACE RBRACE'''
    p[0] = StructInit(p[1], [], *_pos(p, 1))


def p_campo_inits_muchos(p):
    '''campo_inits : campo_init COMMA campo_inits'''
    p[0] = [p[1]] + p[3]


def p_campo_inits_ultimo_coma(p):
    '''campo_inits : campo_init COMMA'''
    p[0] = [p[1]]


def p_campo_inits_ultimo(p):
    '''campo_inits : campo_init'''
    p[0] = [p[1]]


def p_campo_init(p):
    '''campo_init : IDENTIFIER COLON valor_init'''
    p[0] = (p[1], p[3])


# --- Asignacion ---

def p_instruccion_asignacion(p):
    '''instruccion : expresion EQUALS valor_init SEMICOLON'''

    if not _es_target_asignable(p[1]):
        linea = p[1].linea
        columna = p[1].columna

        p.lexer.errors.add(
            'Sintáctico',
            'El lado izquierdo de una asignación '
            'debe ser una ubicación válida de almacenamiento',
            linea,
            columna,
            _fragmento_desde_lexpos(p.lexer, p.lexpos(2))
        )

    p[0] = Assignment(
        p[1],
        p[3],
        *_pos(p, 2)
    )


def p_instruccion_asignacion_compuesta(p):
    '''instruccion : expresion PLUS_ASSIGN expresion SEMICOLON
                   | expresion MINUS_ASSIGN expresion SEMICOLON
                   | expresion TIMES_ASSIGN expresion SEMICOLON
                   | expresion DIVIDE_ASSIGN expresion SEMICOLON
                   | expresion MODULO_ASSIGN expresion SEMICOLON'''

    if not _es_target_asignable(p[1]):
        linea = p[1].linea
        columna = p[1].columna

        p.lexer.errors.add(
            'Sintáctico',
            'El lado izquierdo de una asignación '
            'debe ser una ubicación válida de almacenamiento',
            linea,
            columna,
            _fragmento_desde_lexpos(p.lexer, p.lexpos(2))
        )

    p[0] = CompoundAssignment(
        p[1],
        p[2],
        p[3],
        *_pos(p, 2)
    )

# --- Sentencias de control ---


def p_instruccion_if(p):
    '''instruccion : if_stmt'''
    p[0] = p[1]


def p_if_simple(p):
    '''if_stmt : IF expresion LBRACE instrucciones RBRACE'''

    _validar_condicion_if(p[2], p, 1)

    cuerpo = Block(
        p[4],
        *_pos(p, 3)
    )

    p[0] = IfStmt(
        p[2],
        cuerpo,
        None,
        *_pos(p, 1)
    )


def p_if_else(p):
    '''if_stmt : IF expresion LBRACE instrucciones RBRACE ELSE LBRACE instrucciones RBRACE'''

    _validar_condicion_if(p[2], p, 1)

    cuerpo = Block(
        p[4],
        *_pos(p, 3)
    )

    else_block = Block(
        p[8],
        *_pos(p, 7)
    )

    p[0] = IfStmt(
        p[2],
        cuerpo,
        else_block,
        *_pos(p, 1)
    )


def p_if_else_if(p):
    '''if_stmt : IF expresion LBRACE instrucciones RBRACE ELSE if_stmt'''

    _validar_condicion_if(p[2], p, 1)

    cuerpo = Block(
        p[4],
        *_pos(p, 3)
    )

    p[0] = IfStmt(
        p[2],
        cuerpo,
        p[7],
        *_pos(p, 1)
    )

def p_instruccion_while(p):
    '''instruccion : WHILE expresion LBRACE instrucciones RBRACE'''
    cuerpo = Block(p[4], *_pos(p, 3))
    p[0] = WhileStmt(p[2], cuerpo, *_pos(p, 1))


def p_instruccion_loop(p):
    '''instruccion : LOOP LBRACE instrucciones RBRACE'''
    cuerpo = Block(p[3], *_pos(p, 2))
    p[0] = LoopStmt(None, cuerpo, *_pos(p, 1))


def p_instruccion_loop_label(p):
    '''instruccion : LABEL COLON LOOP LBRACE instrucciones RBRACE'''
    cuerpo = Block(p[5], *_pos(p, 4))
    p[0] = LoopStmt(p[1], cuerpo, *_pos(p, 1))


def p_instruccion_match(p):
    '''instruccion : MATCH expresion LBRACE match_arms RBRACE'''
    linea, col = _pos(p, 1)

    tiene_wildcard = any(
        isinstance(arm.patron, Identifier)
        and arm.patron.nombre == '_'
        for arm in p[4]
    )

    if not tiene_wildcard:
        p.lexer.errors.add(
            'Sintáctico',
            "La sentencia match debe incluir el patrón comodín '_'",
            linea,
            col,
            _fragmento_desde_lexpos(
                p.lexer,
                p.lexpos(1)
            )
        )

    p[0] = MatchStmt(
        p[2],
        p[4],
        linea,
        col
    )


def p_match_arms_muchos(p):
    '''match_arms : match_arm COMMA match_arms'''
    p[0] = [p[1]] + p[3]


def p_match_arms_ultimo_coma(p):
    '''match_arms : match_arm COMMA'''
    p[0] = [p[1]]


def p_match_arms_ultimo(p):
    '''match_arms : match_arm'''
    p[0] = [p[1]]


def p_match_arm(p):
    '''match_arm : match_pattern FAT_ARROW match_body'''
    p[0] = MatchArm(p[1], p[3], p[1].linea, p[1].columna)


def p_match_pattern_expr(p):
    '''match_pattern : expresion'''
    p[0] = p[1]


def p_match_pattern_wildcard(p):
    '''match_pattern : WILDCARD'''
    p[0] = Identifier(
        '_',
        *_pos(p, 1)
    )


def p_match_body_expr(p):
    '''match_body : expresion'''
    p[0] = p[1]


def p_match_body_block(p):
    '''match_body : LBRACE instrucciones RBRACE'''
    p[0] = Block(p[2], *_pos(p, 1))


# --- Sentencias de transferencia ---

def p_instruccion_return_valor(p):
    '''instruccion : RETURN expresion SEMICOLON'''
    p[0] = ReturnStmt(p[2], *_pos(p, 1))


def p_instruccion_return_vacio(p):
    '''instruccion : RETURN SEMICOLON'''
    p[0] = ReturnStmt(None, *_pos(p, 1))


def p_instruccion_break(p):
    '''instruccion : BREAK SEMICOLON'''
    p[0] = BreakStmt(None, *_pos(p, 1))


def p_instruccion_break_label(p):
    '''instruccion : BREAK LABEL SEMICOLON'''
    p[0] = BreakStmt(p[2], *_pos(p, 1))


def p_instruccion_continue(p):
    '''instruccion : CONTINUE SEMICOLON'''
    p[0] = ContinueStmt(None, *_pos(p, 1))


def p_instruccion_continue_label(p):
    '''instruccion : CONTINUE LABEL SEMICOLON'''
    p[0] = ContinueStmt(p[2], *_pos(p, 1))


# --- Expresion como instruccion ---

def p_instruccion_expresion(p):
    '''instruccion : expresion SEMICOLON'''
    p[0] = ExpressionStmt(p[1], p[1].linea, p[1].columna)


# ===================================================================
# EXPRESIONES
# ===================================================================

# --- Literales ---

def p_expresion_int(p):
    '''expresion : NUMBER_INT'''
    p[0] = Literal(
        p[1],
        *_pos(p, 1),
        tipo='i32'
    )


def p_expresion_float(p):
    '''expresion : NUMBER_FLOAT'''
    p[0] = Literal(
        p[1],
        *_pos(p, 1),
        tipo='f64'
    )


def p_expresion_string(p):
    '''expresion : STRING_LITERAL'''
    p[0] = Literal(
        p[1],
        *_pos(p, 1),
        tipo='String'
    )


def p_expresion_char(p):
    '''expresion : CHAR_LITERAL'''
    p[0] = Literal(
        p[1],
        *_pos(p, 1),
        tipo='char'
    )


def p_expresion_true(p):
    '''expresion : TRUE'''
    p[0] = Literal(
        True,
        *_pos(p, 1),
        tipo='bool'
    )


def p_expresion_false(p):
    '''expresion : FALSE'''
    p[0] = Literal(
        False,
        *_pos(p, 1),
        tipo='bool'
    )


# --- Identificador ---

def p_expresion_identifier(p):
    '''expresion : IDENTIFIER'''
    p[0] = Identifier(p[1], *_pos(p, 1))


# --- Operaciones binarias ---

def p_expresion_aritmetica(p):
    '''expresion : expresion PLUS expresion
                 | expresion MINUS expresion
                 | expresion TIMES expresion
                 | expresion DIVIDE expresion
                 | expresion MODULO expresion'''
    p[0] = BinaryOp(p[1], p[2], p[3], *_pos(p, 2))


def p_expresion_comparacion(p):
    '''expresion : expresion EQ expresion
                 | expresion NEQ expresion
                 | expresion LT expresion
                 | expresion LTE expresion
                 | expresion GT expresion
                 | expresion GTE expresion'''
    p[0] = Comparison(p[1], p[2], p[3], *_pos(p, 2))


def p_expresion_logica(p):
    '''expresion : expresion AND expresion
                 | expresion OR expresion'''
    p[0] = LogicalOp(p[1], p[2], p[3], *_pos(p, 2))


# --- Operaciones unarias ---

def p_expresion_not(p):
    '''expresion : NOT expresion'''
    p[0] = UnaryOp('!', p[2], *_pos(p, 1))


def p_expresion_uminus(p):
    '''expresion : MINUS expresion %prec UMINUS'''
    p[0] = UnaryOp('-', p[2], *_pos(p, 1))


# --- Agrupacion ---

def p_expresion_paren(p):
    '''expresion : LPAREN expresion RPAREN'''
    p[0] = p[2]

    # Marcamos que esta expresión estuvo encerrada
    # directamente entre paréntesis.
    p[0]._parenthesized = True


# --- Arreglos ---

def p_expresion_arreglo(p):
    '''expresion : LBRACKET lista_expresiones RBRACKET'''
    p[0] = ArrayLiteral(p[2], *_pos(p, 1))


def p_expresion_arreglo_vacio(p):
    '''expresion : LBRACKET RBRACKET'''
    p[0] = ArrayLiteral([], *_pos(p, 1))


def p_expresion_arreglo_repetido(p):
    '''expresion : LBRACKET expresion SEMICOLON NUMBER_INT RBRACKET'''
    p[0] = ArrayRepeat(
        p[2],
        p[4],
        *_pos(p, 1)
    )


def p_expresion_array_access(p):
    '''expresion : expresion LBRACKET expresion RBRACKET'''
    p[0] = ArrayAccess(p[1], p[3], *_pos(p, 2))


def p_expresion_slice(p):
    '''expresion : AMPERSAND expresion LBRACKET expresion RANGE expresion RBRACKET'''
    p[0] = SliceAccess(p[2], p[4], p[6], *_pos(p, 1))


# --- Acceso a campos y metodos ---

def p_expresion_method_call(p):
    '''expresion : expresion DOT IDENTIFIER LPAREN argumentos RPAREN'''
    p[0] = MethodCall(p[1], p[3], p[5], *_pos(p, 3))


def p_expresion_field_access(p):
    '''expresion : expresion DOT IDENTIFIER'''
    p[0] = FieldAccess(p[1], p[3], *_pos(p, 3))


# --- Llamadas a funciones ---

def p_expresion_function_call(p):
    '''expresion : IDENTIFIER LPAREN argumentos RPAREN'''
    p[0] = FunctionCall(p[1], p[3], *_pos(p, 1))


# --- Constructores de String ---

def p_expresion_string_from(p):
    '''expresion : STRING_TYPE DOUBLE_COLON IDENTIFIER LPAREN STRING_LITERAL RPAREN'''
    linea, col = _pos(p, 1)

    if p[3] != 'from':
        p.lexer.errors.add(
            'Sintáctico',
            f"Constructor de String inválido: String::{p[3]}",
            linea,
            col,
            _fragmento_desde_lexpos(p.lexer, p.lexpos(1))
        )

    argumento = Literal(
        p[5],
        *_pos(p, 5),
        tipo='String'
    )

    p[0] = StringFrom(
        argumento,
        linea,
        col
    )


def p_expresion_string_new(p):
    '''expresion : STRING_TYPE DOUBLE_COLON IDENTIFIER LPAREN RPAREN'''
    linea, col = _pos(p, 1)

    if p[3] != 'new':
        p.lexer.errors.add(
            'Sintáctico',
            f"Constructor de String inválido: String::{p[3]}",
            linea,
            col,
            _fragmento_desde_lexpos(p.lexer, p.lexpos(1))
        )

    p[0] = StringNew(
        linea,
        col
    )


# --- println! ---

def p_expresion_println(p):
    '''expresion : PRINTLN_MACRO LPAREN argumentos RPAREN'''
    p[0] = PrintlnCall(p[3], *_pos(p, 1))


# --- Listas de expresiones ---

def p_argumentos_lista(p):
    '''argumentos : lista_expresiones'''
    p[0] = p[1]


def p_argumentos_vacio(p):
    '''argumentos : '''
    p[0] = []


def p_lista_expresiones_muchas(p):
    '''lista_expresiones : lista_expresiones COMMA expresion'''
    p[0] = p[1] + [p[3]]


def p_lista_expresiones_una(p):
    '''lista_expresiones : expresion'''
    p[0] = [p[1]]


# ===================================================================
# MANEJO DE ERRORES
# ===================================================================

def p_error(p):
    if p is None:
        linea, col, fragmento = _posicion_eof(ox_lexer)

        if hasattr(ox_lexer, 'errors'):
            ox_lexer.errors.add(
                'Sintáctico',
                'Final de archivo inesperado',
                linea,
                col,
                fragmento
            )

        return

    linea = p.lineno
    data = p.lexer.lexdata
    lexpos = p.lexpos

    line_start = data.rfind('\n', 0, lexpos) + 1
    col = (lexpos - line_start) + 1

    line_end = data.find('\n', lexpos)

    if line_end == -1:
        line_end = len(data)

    fragmento = data[line_start:line_end]

    p.lexer.errors.add(
        'Sintáctico',
        f"Token inesperado '{p.value}'",
        linea,
        col,
        fragmento
    )

    # recuperacion: avanzar hasta un punto de sincronizacion
    while True:
        tok = parser.token()
        if tok is None:
            break
        if tok.type in ('SEMICOLON', 'RBRACE'):
            break

    parser.restart()


# ===================================================================
# Construccion y funcion principal
# ===================================================================

parser = yacc.yacc(debug=False, write_tables=False)


def parse(source_code, errors=None):
    """Analiza el codigo fuente y devuelve el AST."""
    if errors is None:
        errors = ErrorList()

    ox_lexer.lineno = 1
    ox_lexer.errors = errors

    resultado = parser.parse(source_code, lexer=ox_lexer)
    return resultado
