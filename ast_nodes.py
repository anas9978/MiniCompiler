"""
ast_nodes.py
------------
Plain dataclasses for every AST node MiniPy can produce. Kept
free of any parsing or evaluation logic so parser.py, semantic.py,
ir_generator.py, and interpreter.py can all import just the shapes
they need to walk.
"""

from dataclasses import dataclass, field


@dataclass
class Program:
    body: list


@dataclass
class Assign:
    name: str
    expr: object
    line: int


@dataclass
class If:
    cond: object
    then_block: list
    else_block: list
    line: int


@dataclass
class While:
    cond: object
    body: list
    line: int


@dataclass
class Print:
    expr: object
    line: int


@dataclass
class BinaryOp:
    op: str
    left: object
    right: object
    line: int


@dataclass
class UnaryOp:
    op: str
    expr: object
    line: int


@dataclass
class Identifier:
    name: str
    line: int


@dataclass
class Number:
    value: float
    line: int
