import ply.lex as lex
from interpreter.errors import ErrorList


# Palabras reservadas
reserved = {
    'fn':       'FN',
    'let':      'LET',
    'mut':      'MUT',
    'if':       'IF',
    'else':     'ELSE',
    'while':    'WHILE',
    'loop':     'LOOP',
    'match':    'MATCH',
    'return':   'RETURN',
    'break':    'BREAK',
    'continue': 'CONTINUE',
    'struct':   'STRUCT',
    'true':     'TRUE',
    'false':    'FALSE',
    'i32':      'I32',
    'f64':      'F64',
    'bool':     'BOOL',
    'char':     'CHAR_TYPE',
    'String':   'STRING_TYPE',
}


# Lista de tokens
tokens = [
    # literales e identificadores
    'IDENTIFIER',
    'NUMBER_INT',
    'NUMBER_FLOAT',
    'STRING_LITERAL',
    'CHAR_LITERAL',
    'LABEL',
    'WILDCARD',

    # macro
    'PRINTLN_MACRO',

    # aritmeticos
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULO',

    # asignacion
    'EQUALS',
    'PLUS_ASSIGN', 'MINUS_ASSIGN', 'TIMES_ASSIGN',
    'DIVIDE_ASSIGN', 'MODULO_ASSIGN',

    # relacionales
    'EQ', 'NEQ', 'GT', 'GTE', 'LT', 'LTE',

    # logicos
    'AND', 'OR', 'NOT',

    # delimitadores
    'LPAREN', 'RPAREN',
    'LBRACE', 'RBRACE',
    'LBRACKET', 'RBRACKET',
    'SEMICOLON', 'COLON', 'COMMA', 'DOT',
    'ARROW', 'FAT_ARROW', 'RANGE',
    'AMPERSAND', 'DOUBLE_COLON',

    # tokens internos (se descartan, nunca llegan al parser)
    'BLOCK_COMMENT', 'LINE_COMMENT', "INVALID_CHAR_LITERAL",
] + list(reserved.values())



# Tokens simples (string rules)

# asignacion compuesta
t_PLUS_ASSIGN   = r'\+='
t_MINUS_ASSIGN  = r'-='
t_TIMES_ASSIGN  = r'\*='
t_DIVIDE_ASSIGN = r'/='
t_MODULO_ASSIGN = r'%='

# relacionales de 2 caracteres
t_EQ  = r'=='
t_NEQ = r'!='
t_GTE = r'>='
t_LTE = r'<='

# logicos de 2 caracteres
t_AND = r'&&'
t_OR  = r'\|\|'

# delimitadores de 2 caracteres
t_ARROW        = r'->'
t_FAT_ARROW    = r'=>'
t_RANGE        = r'\.\.'
t_DOUBLE_COLON = r'::'

# aritmeticos de 1 caracter
t_PLUS   = r'\+'
t_MINUS  = r'-'
t_TIMES  = r'\*'
t_DIVIDE = r'/'
t_MODULO = r'%'

# asignacion y comparacion de 1 caracter
t_EQUALS = r'='
t_GT     = r'>'
t_LT     = r'<'
t_NOT    = r'!'

# delimitadores de 1 caracter
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_LBRACE    = r'\{'
t_RBRACE    = r'\}'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_SEMICOLON = r';'
t_COLON     = r':'
t_COMMA     = r','
t_DOT       = r'\.'
t_AMPERSAND = r'&'

# caracteres ignorados
t_ignore = ' \t'



# Tokens con logica (function rules)
# El orden de definicion determina la prioridad


def t_BLOCK_COMMENT(t):
    r'/\*'

    start_pos = t.lexpos
    pos = t.lexer.lexpos
    data = t.lexer.lexdata

    start_line = t.lexer.lineno
    start_col = _find_column(t.lexer, start_pos)

    while pos < len(data):
        if data[pos] == '\n':
            t.lexer.lineno += 1

        if (
            data[pos] == '*'
            and pos + 1 < len(data)
            and data[pos + 1] == '/'
        ):
            t.lexer.lexpos = pos + 2
            return None

        pos += 1

    # Llegamos al EOF sin encontrar */
    t.lexer.errors.add(
        'Léxico',
        'Comentario de bloque sin cerrar',
        start_line,
        start_col,
        _get_fragment(t.lexer, start_pos)
    )

    # Consumir todo el resto de la entrada
    t.lexer.lexpos = len(data)

    return None


def t_LINE_COMMENT(t):
    r'//[^\n]*'
    pass


def t_PRINTLN_MACRO(t):
    r'println!'
    return t


def t_STRING_LITERAL(t):
    r'r\#"(?:[^"\n]|"(?!\#))*"\#|r"[^"\n]*"|"(?:[^"\\\n]|\\.)*"'

    raw = t.value

    if raw.startswith('r#"'):
        t.value = raw[3:-2]

    elif raw.startswith('r"'):
        t.value = raw[2:-1]

    else:
        t.value = _process_escapes(raw[1:-1])

    return t


def t_CHAR_LITERAL(t):
    r"'(?:[^'\\\n]|\\.)'"

    inner = t.value[1:-1]
    value = _process_escapes(inner)

    if len(value) != 1:
        t.lexer.errors.add(
            'Léxico',
            'Un literal char debe contener exactamente un carácter',
            t.lexer.lineno,
            _find_column(t.lexer, t.lexpos),
            _get_fragment(t.lexer, t.lexpos)
        )
        return None

    t.value = value

    return t


def t_INVALID_CHAR_LITERAL(t):
    r"'(?:[^'\\\n]|\\.)*'"

    t.lexer.errors.add(
        'Léxico',
        'Un literal char debe contener exactamente un carácter',
        t.lexer.lineno,
        _find_column(t.lexer, t.lexpos),
        _get_fragment(t.lexer, t.lexpos)
    )

    return None


def t_LABEL(t):
    r"'[a-zA-Z_][a-zA-Z0-9_]*"
    # quitar la comilla simple del inicio
    t.value = t.value[1:]
    return t


def t_NUMBER_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t


def t_NUMBER_INT(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'

    if t.value == '_':
        t.type = 'WILDCARD'
    else:
        t.type = reserved.get(t.value, 'IDENTIFIER')

    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t):
    col = _find_column(t.lexer, t.lexpos)
    fragment = _get_fragment(t.lexer, t.lexpos)

    t.lexer.errors.add(
        'Léxico',
        f"Carácter no reconocido '{t.value[0]}'",
        t.lexer.lineno,
        col,
        fragment
    )

    t.lexer.skip(1)



# Funciones auxiliares


def _find_column(lexer_obj, lexpos):
    """Calcula la columna 1-indexed."""

    source = lexer_obj.lexdata
    line_start = source.rfind('\n', 0, lexpos) + 1

    return (lexpos - line_start) + 1


def _get_fragment(lexer_obj, lexpos):
    """Devuelve la línea de código donde se encuentra lexpos."""

    source = lexer_obj.lexdata

    line_start = source.rfind('\n', 0, lexpos) + 1

    line_end = source.find('\n', lexpos)

    if line_end == -1:
        line_end = len(source)

    return source[line_start:line_end]


def _process_escapes(text):
    """Reemplaza secuencias de escape dentro de un string."""
    result = []
    i = 0
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt == 'n':
                result.append('\n')
            elif nxt == '\\':
                result.append('\\')
            elif nxt == '"':
                result.append('"')
            else:
                # secuencia no reconocida, dejar tal cual
                result.append(text[i])
                result.append(nxt)
            i += 2
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


# Construccion del lexer y funcion principal


lexer = lex.lex()
lexer.errors = ErrorList()


def tokenize(source_code, errors=None):
    """Recibe código fuente y devuelve la lista de tokens."""

    if errors is None:
        errors = ErrorList()

    lexer.lineno = 1
    lexer.errors = errors
    lexer.input(source_code)

    result = []

    while True:
        tok = lexer.token()

        if not tok:
            break

        result.append(tok)

    return result