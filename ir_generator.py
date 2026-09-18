"""
ir_generator.py
----------------
Lowers the AST into linear Three-Address Code (TAC): every
instruction does at most one operation, using temporaries
(t1, t2, ...) and jump labels (L1, L2, ...). This is the same
shape real compilers use before register allocation, and it's
kept separate from interpreter.py — this module only *generates
text*, it never evaluates anything.
"""

from ast_nodes import Assign, If, While, Print, BinaryOp, UnaryOp, Identifier, Number


class IRGenerator:
    def __init__(self):
        self.lines: list[str] = []
        self._temp_count = 0
        self._label_count = 0

    def new_temp(self) -> str:
        self._temp_count += 1
        return f"t{self._temp_count}"

    def new_label(self) -> str:
        self._label_count += 1
        return f"L{self._label_count}"

    def emit(self, text: str):
        self.lines.append(text)

    def gen_expr(self, node) -> str:
        if isinstance(node, Number):
            return _format_number(node.value)
        if isinstance(node, Identifier):
            return node.name
        if isinstance(node, UnaryOp):
            val = self.gen_expr(node.expr)
            t = self.new_temp()
            self.emit(f"{t} = -{val}")
            return t
        if isinstance(node, BinaryOp):
            left = self.gen_expr(node.left)
            right = self.gen_expr(node.right)
            t = self.new_temp()
            self.emit(f"{t} = {left} {node.op} {right}")
            return t
        raise ValueError(f"gen_expr: unknown node type {type(node).__name__}")

    def gen_stmt(self, node):
        if isinstance(node, Assign):
            val = self.gen_expr(node.expr)
            self.emit(f"{node.name} = {val}")
        elif isinstance(node, Print):
            val = self.gen_expr(node.expr)
            self.emit(f"print {val}")
        elif isinstance(node, If):
            cond_val = self.gen_expr(node.cond)
            true_label = self.new_label()
            false_label = self.new_label()
            end_label = self.new_label()
            self.emit(f"if {cond_val} goto {true_label}")
            self.emit(f"goto {false_label}")
            self.emit(f"{true_label}:")
            for s in node.then_block:
                self.gen_stmt(s)
            self.emit(f"goto {end_label}")
            self.emit(f"{false_label}:")
            for s in node.else_block:
                self.gen_stmt(s)
            self.emit(f"{end_label}:")
        elif isinstance(node, While):
            start_label = self.new_label()
            body_label = self.new_label()
            end_label = self.new_label()
            self.emit(f"{start_label}:")
            cond_val = self.gen_expr(node.cond)
            self.emit(f"if {cond_val} goto {body_label}")
            self.emit(f"goto {end_label}")
            self.emit(f"{body_label}:")
            for s in node.body:
                self.gen_stmt(s)
            self.emit(f"goto {start_label}")
            self.emit(f"{end_label}:")
        else:
            raise ValueError(f"gen_stmt: unknown node type {type(node).__name__}")


def _format_number(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def generate_tac(program) -> list[str]:
    gen = IRGenerator()
    for stmt in program.body:
        gen.gen_stmt(stmt)
    return gen.lines
