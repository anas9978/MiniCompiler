"""
lexer.py
--------
Converts MiniPy source text into a flat list of Tokens.

Handles Python-style indentation by emitting INDENT/DEDENT tokens
whenever the leading-whitespace depth of a line changes, which is
what lets the parser treat blocks the same way Python's own does.
"""

import re
from tokens import Token, TokenType, KEYWORDS
from errors import LexError

_TWO_CHAR_OPS = {
    "==": TokenType.EQ,
    "!=": TokenType.NE,
    "<=": TokenType.LE,
    ">=": TokenType.GE,
}

_ONE_CHAR_OPS = {
    "=": TokenType.ASSIGN,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "%": TokenType.PERCENT,
    "<": TokenType.LT,
    ">": TokenType.GT,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    ":": TokenType.COLON,
    ",": TokenType.COMMA,
}

_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_NUMBER_RE = re.compile(r"[0-9]+(\.[0-9]+)?")


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    lines = source.replace("\r\n", "\n").split("\n")
    indent_stack = [0]

    for line_no, raw_line in enumerate(lines, start=1):
        # Strip comments
        comment_idx = raw_line.find("#")
        code_part = raw_line if comment_idx < 0 else raw_line[:comment_idx]

        if code_part.strip() == "":
            continue  # blank / comment-only line: no tokens, no indent change

        # Measure indentation (tabs count as 4 spaces)
        i = 0
        indent = 0
        while i < len(code_part) and code_part[i] in (" ", "\t"):
            indent += 4 if code_part[i] == "\t" else 1
            i += 1

        if indent > indent_stack[-1]:
            indent_stack.append(indent)
            tokens.append(Token(TokenType.INDENT, indent, line_no, 1))
        else:
            while indent < indent_stack[-1]:
                indent_stack.pop()
                tokens.append(Token(TokenType.DEDENT, indent, line_no, 1))
            if indent != indent_stack[-1]:
                raise LexError("Inconsistent indentation", line_no, 1)

        col = i + 1
        while i < len(code_part):
            ch = code_part[i]

            if ch in (" ", "\t"):
                i += 1
                col += 1
                continue

            m = _NUMBER_RE.match(code_part, i)
            if m:
                text = m.group(0)
                value = float(text) if "." in text else int(text)
                tokens.append(Token(TokenType.NUMBER, value, line_no, col))
                i += len(text)
                col += len(text)
                continue

            m = _IDENT_RE.match(code_part, i)
            if m:
                text = m.group(0)
                ttype = KEYWORDS.get(text, TokenType.IDENTIFIER)
                tokens.append(Token(ttype, text, line_no, col))
                i += len(text)
                col += len(text)
                continue

            two = code_part[i:i + 2]
            if two in _TWO_CHAR_OPS:
                tokens.append(Token(_TWO_CHAR_OPS[two], two, line_no, col))
                i += 2
                col += 2
                continue

            one = code_part[i]
            if one in _ONE_CHAR_OPS:
                tokens.append(Token(_ONE_CHAR_OPS[one], one, line_no, col))
                i += 1
                col += 1
                continue

            raise LexError(f"Unexpected character '{ch}'", line_no, col)

        tokens.append(Token(TokenType.NEWLINE, "\\n", line_no, col))

    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(Token(TokenType.DEDENT, 0, len(lines) + 1, 1))
    tokens.append(Token(TokenType.EOF, None, len(lines) + 1, 1))

    return tokens
