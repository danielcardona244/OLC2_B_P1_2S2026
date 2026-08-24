class ErrorItem:
    """Representa un error detectado durante el analisis o la ejecucion."""

    def __init__(self, tipo, descripcion, linea, columna, fragmento=''):
        self.tipo = tipo
        self.descripcion = descripcion
        self.linea = linea
        self.columna = columna
        self.fragmento = fragmento

    def __repr__(self):
        return (
            f"[Error {self.tipo}] Linea {self.linea}, "
            f"Columna {self.columna} {self.descripcion}"
        )

    def to_dict(self):
        return {
            'tipo': self.tipo,
            'descripcion': self.descripcion,
            'linea': self.linea,
            'columna': self.columna,
            'fragmento': self.fragmento,
        }


class ErrorList:

    def __init__(self):
        self.errors = []

    def add(self, tipo, descripcion, linea, columna, fragmento=''):
        self.errors.append(
            ErrorItem(
                tipo,
                descripcion,
                linea,
                columna,
                fragmento
            )
        )

    def clear(self):
        self.errors.clear()

    def get_all(self):
        return list(self.errors)

    def has_errors(self):
        return bool(self.errors)