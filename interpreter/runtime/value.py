from copy import deepcopy


class RuntimeValue:
    """Valor producido durante la ejecución de OxigenScript."""

    def __init__(self, value=None, tipo=None):
        self.value = value
        self.tipo = tipo

    def clone(self):
        return deepcopy(self)

    def __repr__(self):
        return f"RuntimeValue(value={self.value!r}, tipo={self.tipo!r})"


class RuntimeVariable:
    """Variable almacenada en un entorno de ejecución."""

    def __init__(self, nombre, valor=None, mutable=False, initialized=True):
        self.nombre = nombre
        self.valor = valor if valor is not None else RuntimeValue()
        self.mutable = mutable
        self.initialized = initialized

    def __repr__(self):
        return (
            f"RuntimeVariable(nombre={self.nombre!r}, "
            f"valor={self.valor!r}, mutable={self.mutable!r}, "
            f"initialized={self.initialized!r})"
        )
