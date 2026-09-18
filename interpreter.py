"""
interpreter.py
--------------
Executes the AST directly to produce MiniPy's actual program
output. This is a *safe* interpreter: it only understands the AST
node types defined in ast_nodes.py, so there is no path to
arbitrary Python execution (no eval/exec of user input anywhere).

Kept separate from ir_generator.py on purpose: that module emits
TAC for *display* (what a real compiler would hand to a backend
next), while this module actually runs the program so the Output
tab is always correct.
"""

from ast_nodes import Assign, If, While, Print, BinaryOp, UnaryOp, Identifier, Number
from errors import InterpreterError

MAX_STEPS = 200_000  # guards against infinite loops, e.g. `while 1:`


class Interpreter:
    def __init__(self, max_steps: int = MAX_STEPS):
        self.env: dict[str, float] = {}
        self.output: list[str] = []
        self._steps = 0
        self._max_steps = max_steps

    def _step(self, line):
        self._steps += 1
        if self._steps > self._max_steps:
            raise InterpreterError(
                "Execution aborted: too many steps (possible infinite loop)", line
            )

    def eval_expr(self, node):
        if isinstance(node, Number):
            return node.value
        if isinstance(node, Identifier):
            if node.name not in self.env:
                raise InterpreterError(f"Name '{node.name}' is not defined", node.line)
            return self.env[node.name]
        if isinstance(node, UnaryOp):
            return -self.eval_expr(node.expr)
        if isinstance(node, BinaryOp):
            left = self.eval_expr(node.left)
            right = self.eval_expr(node.right)
            op = node.op
            if op == "+":
                return left + right
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    raise InterpreterError("Division by zero", node.line)
                return float(int(left) // int(right)) if float(left).is_integer() and float(right).is_integer() else left / right
            if op == "%":
                if right == 0:
                    raise InterpreterError("Modulo by zero", node.line)
                return left % right
            if op == "<":
                return 1 if left < right else 0
            if op == ">":
                return 1 if left > right else 0
            if op == "<=":
                return 1 if left <= right else 0
            if op == ">=":
                return 1 if left >= right else 0
            if op == "==":
                return 1 if left == right else 0
            if op == "!=":
                return 1 if left != right else 0
            raise InterpreterError(f"Unknown operator '{op}'", node.line)
        raise InterpreterError(f"Cannot evaluate node type {type(node).__name__}", getattr(node, "line", 0))

    def exec_stmt(self, node):
        self._step(node.line)
        if isinstance(node, Assign):
            self.env[node.name] = self.eval_expr(node.expr)
        elif isinstance(node, Print):
            self.output.append(_format_value(self.eval_expr(node.expr)))
        elif isinstance(node, If):
            if self.eval_expr(node.cond):
                for s in node.then_block:
                    self.exec_stmt(s)
            else:
                for s in node.else_block:
                    self.exec_stmt(s)
        elif isinstance(node, While):
            while self.eval_expr(node.cond):
                for s in node.body:
                    self.exec_stmt(s)
                self._step(node.line)
        else:
            raise InterpreterError(f"Cannot execute node type {type(node).__name__}", getattr(node, "line", 0))


def _format_value(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def interpret(program, max_steps: int = MAX_STEPS) -> list[str]:
    interp = Interpreter(max_steps=max_steps)
    for stmt in program.body:
        interp.exec_stmt(stmt)
    return interp.output
