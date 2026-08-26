class Symbol:
    """Representa un símbolo registrado durante el análisis semántico."""

    def __init__(
        self,
        nombre,
        tipo,
        categoria,
        mutable=False,
        valor=None,
        linea=0,
        columna=0,
        ambito='global'
    ):
        self.nombre = nombre
        self.tipo = tipo
        self.categoria = categoria
        self.mutable = mutable
        self.valor = valor
        self.linea = linea
        self.columna = columna
        self.ambito = ambito

    def __repr__(self):
        return (
            f"Symbol("
            f"nombre={self.nombre!r}, "
            f"tipo={self.tipo!r}, "
            f"categoria={self.categoria!r}, "
            f"ambito={self.ambito!r}"
            f")"
        )

    def to_dict(self):
        return {
            'nombre': self.nombre,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'mutable': self.mutable,
            'valor': self.valor,
            'linea': self.linea,
            'columna': self.columna,
            'ambito': self.ambito,
        }