from interpreter.runtime.value import RuntimeValue, RuntimeVariable


class RuntimeEnvironment:
    """Entorno léxico usado únicamente durante la ejecución."""

    def __init__(self, nombre='global', padre=None):
        self.nombre = nombre
        self.padre = padre
        self.variables = {}

    def create_child(self, nombre):
        return RuntimeEnvironment(
            nombre=nombre,
            padre=self,
        )

    def define(self, nombre, valor=None, mutable=False, initialized=True):
        variable = RuntimeVariable(
            nombre=nombre,
            valor=valor if valor is not None else RuntimeValue(),
            mutable=mutable,
            initialized=initialized,
        )

        # OxigenScript permite shadowing. Una declaración nueva en el
        # mismo scope reemplaza la entrada visible en ese scope.
        self.variables[nombre] = variable
        return variable

    def lookup_local(self, nombre):
        return self.variables.get(nombre)

    def lookup(self, nombre):
        actual = self

        while actual is not None:
            if nombre in actual.variables:
                return actual.variables[nombre]

            actual = actual.padre

        return None
