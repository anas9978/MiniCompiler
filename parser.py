"""
parser.py
---------
Recursive-descent parser. Consumes the token list from lexer.py
and builds an AST out of the node types in ast_nodes.py.

Grammar (informal):
    program    := statement*
    statement  := assign | if_stmt | while_stmt | print_stmt
    assign     := IDENTIFIER '=' expr NEWLINE
    if_stmt    := 'if' expr ':' block ('else' ':' block)?
    while_stmt := 'while' expr ':' block
    print_stmt := 'print' '(' expr ')' NEWLINE
    block      := NEWLINE INDENT statement+ DEDENT
    expr       := comparison
    comparison := add_expr ((< | > | <= | >= | == | !=) add_expr)?
    add_expr   := mul_expr (('+' | '-') mul_expr)*
    mul_expr   := unary (('*' | '/' | '%') unary)*
    unary      := '-' unary | primary
    primary    := NUMBER | IDENTIFIER | '(' expr ')'
"""

from tokens import TokenType
from ast_nodes import (
    Program, Assign, If, While, Print, BinaryOp, UnaryOp, Identifier, Number,
)
from errors import ParserError

_COMPARISON_OPS = {
    TokenType.LT, TokenType.GT, TokenType.LE,
    TokenType.GE, TokenType.EQ, TokenType.NE,
}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def check(self, ttype):
        return self.current().type == ttype

    def expect(self, ttype, message=None):
        if self.check(ttype):
            return self.advance()
        tok = self.current()
        raise ParserError(
            message or f"Expected {ttype.name} but got {tok.type.name} ('{tok.value}')",
            tok.line,
        )

    def parse_program(self):
        body = []
        while not self.check(TokenType.EOF):
            if self.check(TokenType.NEWLINE):
                self.advance()
                continue
            body.append(self.parse_statement())
        return Program(body)

    def parse_block(self):
        self.expect(TokenType.NEWLINE, "Expected newline before indented block")
        self.expect(TokenType.INDENT, "Expected an indented block")
        stmts = []
        while not self.check(TokenType.DEDENT) and not self.check(TokenType.EOF):
            if self.check(TokenType.NEWLINE):
                self.advance()
                continue
            stmts.append(self.parse_statement())
        self.expect(TokenType.DEDENT, "Expected end of indented block")
        return stmts

    def parse_statement(self):
        tok = self.current()
        if tok.type == TokenType.IF:
            return self.parse_if()
        if tok.type == TokenType.WHILE:
            return self.parse_while()
        if tok.type == TokenType.PRINT:
            return self.parse_print()
        if tok.type == TokenType.IDENTIFIER:
            return self.parse_assign()
        raise ParserError(f"Unexpected token '{tok.value}' at start of statement", tok.line)

    def parse_assign(self):
        name_tok = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.ASSIGN, f"Expected '=' after identifier '{name_tok.value}'")
        expr = self.parse_expr()
        self.expect(TokenType.NEWLINE, "Expected newline after statement")
        return Assign(name_tok.value, expr, name_tok.line)

    def parse_if(self):
        if_tok = self.expect(TokenType.IF)
        cond = self.parse_expr()
        self.expect(TokenType.COLON, "Expected ':' after if-condition")
        then_block = self.parse_block()
        else_block = []
        if self.check(TokenType.ELSE):
            self.advance()
            self.expect(TokenType.COLON, "Expected ':' after else")
            else_block = self.parse_block()
        return If(cond, then_block, else_block, if_tok.line)

    def parse_while(self):
        while_tok = self.expect(TokenType.WHILE)
        cond = self.parse_expr()
        self.expect(TokenType.COLON, "Expected ':' after while-condition")
        body = self.parse_block()
        return While(cond, body, while_tok.line)

    def parse_print(self):
        print_tok = self.expect(TokenType.PRINT)
        self.expect(TokenType.LPAREN, "Expected '(' after print")
        expr = self.parse_expr()
        self.expect(TokenType.RPAREN, "Expected ')' to close print(...)")
        self.expect(TokenType.NEWLINE, "Expected newline after statement")
        return Print(expr, print_tok.line)

    def parse_expr(self):
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_add_expr()
        if self.current().type in _COMPARISON_OPS:
            op_tok = self.advance()
            right = self.parse_add_expr()
            left = BinaryOp(op_tok.value, left, right, op_tok.line)
        return left

    def parse_add_expr(self):
        left = self.parse_mul_expr()
        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            op_tok = self.advance()
            right = self.parse_mul_expr()
            left = BinaryOp(op_tok.value, left, right, op_tok.line)
        return left

    def parse_mul_expr(self):
        left = self.parse_unary()
        while self.check(TokenType.STAR) or self.check(TokenType.SLASH) or self.check(TokenType.PERCENT):
            op_tok = self.advance()
            right = self.parse_unary()
            left = BinaryOp(op_tok.value, left, right, op_tok.line)
        return left

    def parse_unary(self):
        if self.check(TokenType.MINUS):
            op_tok = self.advance()
            expr = self.parse_unary()
            return UnaryOp("-", expr, op_tok.line)
        return self.parse_primary()

    def parse_primary(self):
        tok = self.current()
        if tok.type == TokenType.NUMBER:
            self.advance()
            return Number(tok.value, tok.line)
        if tok.type == TokenType.IDENTIFIER:
            self.advance()
            return Identifier(tok.value, tok.line)
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN, "Expected ')' to close expression")
            return expr
        raise ParserError(f"Unexpected token '{tok.value}' in expression", tok.line)


def parse(tokens):
    return Parser(tokens).parse_program()
