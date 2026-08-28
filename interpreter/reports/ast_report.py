import shutil
import subprocess
from pathlib import Path

class AstReport:
    def __init__(self):
        self.counter = 0
        self.lines = []

    def to_dot(self, ast):
        self.counter = 0
        self.lines = [
            'digraph OxigenScriptAST {',
            '  rankdir=TB;',
            '  graph [bgcolor="white"];',
            '  node [shape=box, fontname="Arial"];',
            '  edge [fontname="Arial"];',
        ]
        if ast is not None:
            self._visit(ast, None, None)
        self.lines.append('}')
        return '\n'.join(self.lines)

    def write_dot(self, ast, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_dot(ast), encoding='utf-8')
        return path

    def render_svg(self, ast, svg_path):
        executable = shutil.which('dot')
        if executable is None:
            return None
        svg_path = Path(svg_path)
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        process = subprocess.run(
            [executable, '-Tsvg', '-o', str(svg_path)],
            input=self.to_dot(ast),
            text=True,
            capture_output=True,
            check=False,
        )
        if process.returncode != 0:
            raise RuntimeError('Graphviz no pudo generar el SVG: ' + process.stderr.strip())
        return svg_path

    def _next_id(self):
        node_id = f'n{self.counter}'
        self.counter += 1
        return node_id

    def _visit(self, value, parent_id, edge_label):
        if self._is_ast_node(value):
            return self._visit_ast_node(value, parent_id, edge_label)
        if isinstance(value, list):
            return self._visit_sequence(value, parent_id, edge_label or 'lista')
        if isinstance(value, tuple):
            return self._visit_sequence(list(value), parent_id, edge_label or 'tupla')
        if isinstance(value, dict):
            return self._visit_dict(value, parent_id, edge_label or 'dict')
        return self._visit_scalar(value, parent_id, edge_label)

    def _visit_ast_node(self, node, parent_id, edge_label):
        node_id = self._next_id()
        scalar_fields = []
        for name, value in vars(node).items():
            if name.startswith('_') or name in ('linea', 'columna'):
                continue
            if self._is_container_or_ast(value):
                continue
            scalar_fields.append(f'{name}={self._scalar_label(value)}')
        label = '\\n'.join([type(node).__name__, *scalar_fields])
        self.lines.append(f'  {node_id} [label="{self._escape(label)}"];')
        self._connect(parent_id, node_id, edge_label)
        for name, value in vars(node).items():
            if name.startswith('_') or name in ('linea', 'columna'):
                continue
            if self._is_container_or_ast(value):
                self._visit(value, node_id, name)
        return node_id

    def _visit_sequence(self, values, parent_id, edge_label):
        node_id = self._next_id()
        self.lines.append(f'  {node_id} [label="{self._escape(edge_label)}", shape=folder];')
        self._connect(parent_id, node_id, edge_label)
        for index, item in enumerate(values):
            self._visit(item, node_id, str(index))
        return node_id

    def _visit_dict(self, values, parent_id, edge_label):
        node_id = self._next_id()
        self.lines.append(f'  {node_id} [label="{self._escape(edge_label)}", shape=folder];')
        self._connect(parent_id, node_id, edge_label)
        for key, value in values.items():
            self._visit(value, node_id, str(key))
        return node_id

    def _visit_scalar(self, value, parent_id, edge_label):
        node_id = self._next_id()
        self.lines.append(f'  {node_id} [label="{self._escape(self._scalar_label(value))}", shape=ellipse];')
        self._connect(parent_id, node_id, edge_label)
        return node_id

    def _connect(self, parent_id, child_id, label):
        if parent_id is None:
            return
        if label:
            self.lines.append(f'  {parent_id} -> {child_id} [label="{self._escape(label)}"];')
        else:
            self.lines.append(f'  {parent_id} -> {child_id};')

    @staticmethod
    def _is_ast_node(value):
        return (
            value is not None
            and hasattr(value, 'linea')
            and hasattr(value, 'columna')
            and hasattr(value, '__dict__')
        )

    @classmethod
    def _is_container_or_ast(cls, value):
        return cls._is_ast_node(value) or isinstance(value, (list, tuple, dict))

    @staticmethod
    def _scalar_label(value):
        if value is None:
            return 'None'
        if isinstance(value, bool):
            return 'true' if value else 'false'
        return str(value)

    @staticmethod
    def _escape(value):
        return (
            str(value)
            .replace('\\', '\\\\')
            .replace('"', '\\"')
            .replace('\n', '\\n')
            .replace('\r', '')
        )
