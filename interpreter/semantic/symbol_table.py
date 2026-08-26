class SymbolTable:
    """
    Mantiene el historial de símbolos registrados.

    A diferencia de Environment, no se utiliza para resolver nombres.
    Su función principal será alimentar el reporte de tabla de símbolos.
    """

    def __init__(self):
        self.symbols = []

    def add(self, symbol):
        self.symbols.append(symbol)

    def clear(self):
        self.symbols.clear()

    def get_all(self):
        return list(self.symbols)

    def to_list(self):
        return [
            symbol.to_dict()
            for symbol in self.symbols
        ]