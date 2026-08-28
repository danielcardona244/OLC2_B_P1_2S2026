class ReturnSignal(Exception):
    def __init__(self, value):
        super().__init__()
        self.value = value


class BreakSignal(Exception):
    def __init__(self, label=None):
        super().__init__()
        self.label = label


class ContinueSignal(Exception):
    def __init__(self, label=None):
        super().__init__()
        self.label = label
