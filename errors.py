"""
errors.py
---------
One exception type per compiler phase, so app.py can catch each
phase independently and report "which phase failed" rather than
a single generic error.
"""


class CompilerError(Exception):
    """Base class for all MiniPy compiler errors."""

    def __init__(self, message: str, line: int = 0, col: int = 0):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col


class LexError(CompilerError):
    phase = "Lexical Analysis"


class ParserError(CompilerError):
    phase = "Syntax Analysis"


class SemanticError(CompilerError):
    phase = "Semantic Analysis"


class InterpreterError(CompilerError):
    """Raised for runtime failures during execution (not Python's builtin RuntimeError)."""
    phase = "Execution"
