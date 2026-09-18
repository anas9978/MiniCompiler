"""
symbol_table.py
----------------
A minimal symbol table: MiniPy has only global scope and only one
type ('int'), so this is intentionally small. It's still its own
module so semantic.py stays focused on *analysis* and this file
stays focused on *storage* — the same seam a real compiler keeps
between "what's declared" and "is this program valid".
"""

from dataclasses import dataclass


@dataclass
class SymbolEntry:
    name: str
    type: str
    scope: str
    line: int


class SymbolTable:
    def __init__(self):
        self._entries: dict[str, SymbolEntry] = {}

    def declare(self, name: str, line: int, type_: str = "int", scope: str = "global"):
        if name not in self._entries:
            self._entries[name] = SymbolEntry(name, type_, scope, line)

    def is_declared(self, name: str) -> bool:
        return name in self._entries

    def entries(self) -> list[SymbolEntry]:
        return list(self._entries.values())
