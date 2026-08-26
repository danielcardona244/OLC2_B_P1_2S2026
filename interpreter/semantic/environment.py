from interpreter.semantic.symbol_table import SymbolTable


class Environment:
    """Representa un ámbito léxico de OxigenScript."""

    def __init__(
        self,
        nombre='global',
        padre=None,
        errors=None,
        symbol_table=None
    ):
        self.nombre = nombre
        self.padre = padre
        self.errors = errors

        self.symbols = {}

        if symbol_table is None:
            self.symbol_table = SymbolTable()
        else:
            self.symbol_table = symbol_table


    def define(self, symbol, fragmento='', allow_shadowing=False):
        """
        Declara un símbolo en el ámbito actual.

        Por defecto no permite duplicados.
        Las variables pueden habilitar shadowing explícitamente.
        """

        existe = symbol.nombre in self.symbols

        if existe and not allow_shadowing:

            if self.errors is not None:
                self.errors.add(
                    'Semántico',
                    (
                        f"El identificador '{symbol.nombre}' "
                        f"ya fue declarado en este ámbito."
                    ),
                    symbol.linea,
                    symbol.columna,
                    fragmento
                )

            return False

        symbol.ambito = self.nombre

        # Si hay shadowing, la nueva declaración pasa a ser
        # la visible en este entorno.
        self.symbols[symbol.nombre] = symbol

        # La tabla histórica conserva ambas declaraciones.
        self.symbol_table.add(symbol)

        return True


    def lookup_local(self, nombre):
        """Busca únicamente en el ámbito actual."""
        return self.symbols.get(nombre)


    def lookup(self, nombre):
        """
        Busca un símbolo comenzando en el ámbito actual
        y subiendo por la cadena de entornos.
        """

        actual = self

        while actual is not None:

            if nombre in actual.symbols:
                return actual.symbols[nombre]

            actual = actual.padre

        return None


    def create_child(self, nombre):
        """Crea un ámbito hijo que comparte errores y tabla de símbolos."""

        return Environment(
            nombre=nombre,
            padre=self,
            errors=self.errors,
            symbol_table=self.symbol_table
        )