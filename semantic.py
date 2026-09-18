"""
semantic.py
-----------
Walks the AST to build a symbol table and catch errors the parser
can't see: undeclared variables and statically-knowable division
by zero. Everything in MiniPy is an 'int', so there's no type
mismatch checking yet — that's a seam left open deliberately for
extending the language later without restructuring this file.
"""

from ast_nodes import Assign, If, While, Print, BinaryOp, UnaryOp, Identifier, Number
from symbol_table import SymbolTable


class SemanticResult:
    def __init__(self, symbol_table: SymbolTable, errors: list[dict]):
        self.symbol_table = symbol_table
        self.errors = errors


def analyze(program) -> SemanticResult:
    symbol_table = SymbolTable()
    errors: list[dict] = []

    def check_used(name, line):
        if not symbol_table.is_declared(name):
            errors.append({"message": f"Name '{name}' is used before it is assigned", "line": line})

    def walk_expr(node):
        if isinstance(node, Identifier):
            check_used(node.name, node.line)
        elif isinstance(node, BinaryOp):
            walk_expr(node.left)
            walk_expr(node.right)
            if node.op == "/" and isinstance(node.right, Number) and node.right.value == 0:
                errors.append({"message": "Division by zero", "line": node.line})
        elif isinstance(node, UnaryOp):
            walk_expr(node.expr)
        # Number: nothing to check

    def walk_stmt(node):
        if isinstance(node, Assign):
            walk_expr(node.expr)
            symbol_table.declare(node.name, node.line)
        elif isinstance(node, If):
            walk_expr(node.cond)
            for s in node.then_block:
                walk_stmt(s)
            for s in node.else_block:
                walk_stmt(s)
        elif isinstance(node, While):
            walk_expr(node.cond)
            for s in node.body:
                walk_stmt(s)
        elif isinstance(node, Print):
            walk_expr(node.expr)

    for stmt in program.body:
        walk_stmt(stmt)

    return SemanticResult(symbol_table, errors)
