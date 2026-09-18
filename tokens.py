"""
tokens.py
---------
Defines the TokenType enum and the Token record produced by the
lexer. Kept separate from lexer.py so parser.py and app.py can
import token *types* without pulling in lexing logic.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    # Literals / identifiers
    IDENTIFIER = auto()
    NUMBER = auto()

    # Keywords
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    PRINT = auto()

    # Operators
    ASSIGN = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    EQ = auto()
    NE = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    COLON = auto()
    COMMA = auto()

    # Structural
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()


KEYWORDS = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "print": TokenType.PRINT,
}


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.col})"
