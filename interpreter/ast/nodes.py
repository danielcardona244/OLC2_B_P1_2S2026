# Nodos del AST para OxigenScript


class Nodo:
    """Base de todos los nodos del AST."""

    def __init__(self, linea, columna):
        self.linea = linea
        self.columna = columna

    def __repr__(self):
        return f"{type(self).__name__}(linea={self.linea}, col={self.columna})"


# -------------------------------------------------------------------
# Expresiones - producen un valor
# -------------------------------------------------------------------

class Expresion(Nodo):
    pass


class Literal(Expresion):

    def __init__(self, valor, linea, columna, tipo=None):
        super().__init__(linea, columna)
        self.valor = valor
        self.tipo = tipo


class Identifier(Expresion):

    def __init__(self, nombre, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre


class BinaryOp(Expresion):

    def __init__(self, izq, op, der, linea, columna):
        super().__init__(linea, columna)
        self.izq = izq
        self.op = op
        self.der = der


class UnaryOp(Expresion):

    def __init__(self, op, operando, linea, columna):
        super().__init__(linea, columna)
        self.op = op
        self.operando = operando


class Comparison(Expresion):

    def __init__(self, izq, op, der, linea, columna):
        super().__init__(linea, columna)
        self.izq = izq
        self.op = op
        self.der = der


class LogicalOp(Expresion):

    def __init__(self, izq, op, der, linea, columna):
        super().__init__(linea, columna)
        self.izq = izq
        self.op = op
        self.der = der


class ArrayLiteral(Expresion):

    def __init__(self, elementos, linea, columna):
        super().__init__(linea, columna)
        self.elementos = elementos


class ArrayRepeat(Expresion):
    """Arreglo construido repitiendo una expresion N veces: [valor; cantidad]."""

    def __init__(self, valor, cantidad, linea, columna):
        super().__init__(linea, columna)
        self.valor = valor
        self.cantidad = cantidad


class ArrayAccess(Expresion):

    def __init__(self, arreglo, indice, linea, columna):
        super().__init__(linea, columna)
        self.arreglo = arreglo
        self.indice = indice


class SliceAccess(Expresion):

    def __init__(self, arreglo, inicio, fin, linea, columna):
        super().__init__(linea, columna)
        self.arreglo = arreglo
        self.inicio = inicio
        self.fin = fin


class FieldAccess(Expresion):

    def __init__(self, objeto, campo, linea, columna):
        super().__init__(linea, columna)
        self.objeto = objeto
        self.campo = campo


class FunctionCall(Expresion):

    def __init__(self, nombre, argumentos, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.argumentos = argumentos


class MethodCall(Expresion):

    def __init__(self, objeto, metodo, argumentos, linea, columna):
        super().__init__(linea, columna)
        self.objeto = objeto
        self.metodo = metodo
        self.argumentos = argumentos


class StringFrom(Expresion):

    def __init__(self, argumento, linea, columna):
        super().__init__(linea, columna)
        self.argumento = argumento


class StringNew(Expresion):

    def __init__(self, linea, columna):
        super().__init__(linea, columna)


class PrintlnCall(Expresion):

    def __init__(self, argumentos, linea, columna):
        super().__init__(linea, columna)
        self.argumentos = argumentos


class StructInit(Expresion):
    """Inicializacion de un struct: Point { x: 10, y: 20 }."""

    def __init__(self, nombre, campos, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.campos = campos  # lista de tuplas (nombre_campo, valor)


# -------------------------------------------------------------------
# Instrucciones - producen un efecto
# -------------------------------------------------------------------

class Instruccion(Nodo):
    pass


class Program(Nodo):

    def __init__(self, declaraciones):
        super().__init__(1, 1)
        self.declaraciones = declaraciones


class FunctionDecl(Instruccion):

    def __init__(self, nombre, params, tipo_retorno, cuerpo, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.params = params        # lista de Param
        self.tipo_retorno = tipo_retorno  # str, tuple o None
        self.cuerpo = cuerpo        # Block


class Param(Nodo):

    def __init__(self, nombre, tipo, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.tipo = tipo


class StructDecl(Instruccion):

    def __init__(self, nombre, campos, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.campos = campos  # lista de StructField


class StructField(Nodo):

    def __init__(self, nombre, tipo, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.tipo = tipo


class VarDeclaration(Instruccion):

    def __init__(self, nombre, mutable, tipo, valor, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.mutable = mutable  # bool
        self.tipo = tipo        # str, tuple o None
        self.valor = valor      # Expresion


class Assignment(Instruccion):

    def __init__(self, target, valor, linea, columna):
        super().__init__(linea, columna)
        self.target = target  # Identifier, FieldAccess o ArrayAccess
        self.valor = valor


class CompoundAssignment(Instruccion):

    def __init__(self, target, op, valor, linea, columna):
        super().__init__(linea, columna)
        self.target = target
        self.op = op
        self.valor = valor


class IfStmt(Instruccion):

    def __init__(self, condicion, cuerpo, else_branch, linea, columna):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.cuerpo = cuerpo          # Block
        self.else_branch = else_branch  # Block, IfStmt o None


class WhileStmt(Instruccion):

    def __init__(self, condicion, cuerpo, linea, columna):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.cuerpo = cuerpo  # Block


class LoopStmt(Instruccion):

    def __init__(self, etiqueta, cuerpo, linea, columna):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta  # str o None
        self.cuerpo = cuerpo      # Block


class MatchStmt(Instruccion):

    def __init__(self, expresion, brazos, linea, columna):
        super().__init__(linea, columna)
        self.expresion = expresion
        self.brazos = brazos  # lista de MatchArm


class MatchArm(Nodo):

    def __init__(self, patron, cuerpo, linea, columna):
        super().__init__(linea, columna)
        self.patron = patron  # Literal, Identifier('_'), etc.
        self.cuerpo = cuerpo  # Expresion o Block


class Block(Instruccion):

    def __init__(self, instrucciones, linea, columna):
        super().__init__(linea, columna)
        self.instrucciones = instrucciones


class ReturnStmt(Instruccion):

    def __init__(self, valor, linea, columna):
        super().__init__(linea, columna)
        self.valor = valor  # Expresion o None


class BreakStmt(Instruccion):

    def __init__(self, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta  # str o None


class ContinueStmt(Instruccion):

    def __init__(self, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta  # str o None


class ExpressionStmt(Instruccion):

    def __init__(self, expresion, linea, columna):
        super().__init__(linea, columna)
        self.expresion = expresion
