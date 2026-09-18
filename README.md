# MiniPy Compiler

A visual, web-based compiler for **MiniPy** — a small Python-like language —
built as a Computer Science Compiler Design mini-project. Every phase of a
real compiler is implemented from scratch (no use of Python's own `ast`
module or `eval`/`exec` on user code) and is inspectable through a
Streamlit GUI.

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## What MiniPy supports

```python
x = 10
y = 20
z = x + y * 2

if z > 40:
    print(z)
else:
    print(0)

i = 0
while i < 3:
    print(i)
    i = i + 1
```
Output: `50`, `0`, `1`, `2`

- Assignment, arithmetic (`+ - * / %`), comparisons (`< > <= >= == !=`)
- `if` / `else` with **indentation-based blocks**, like real Python
- `while` loops
- `print(expr)`
- `#` comments

Not supported by design: functions, strings, lists, `elif`, `and`/`or`.
The grammar is deliberately small enough to read in one sitting — see
`parser.py`'s module docstring for the full formal grammar.

## Project structure

```
MiniPyCompiler/
├── app.py              Streamlit GUI — wires the phases together, no compiler logic
├── tokens.py            TokenType enum + Token dataclass
├── lexer.py             Phase 1: source text -> tokens (with INDENT/DEDENT)
├── ast_nodes.py         AST node dataclasses (Program, Assign, If, While, ...)
├── parser.py            Phase 2: recursive-descent parser, tokens -> AST
├── symbol_table.py      Symbol storage (name, type, scope, line)
├── semantic.py          Phase 3: symbol table + undefined-variable / div-by-zero checks
├── ir_generator.py      Phase 4: AST -> three-address code (temps + labels)
├── interpreter.py       Phase 5: safe tree-walking execution, with a step limit
├── errors.py            One exception type per phase (LexError, ParserError, ...)
├── examples/            Sample .mpy programs
├── .streamlit/config.toml   Dark theme by default
└── requirements.txt
```

## Design notes (the seams that matter)

- **Codegen vs. execution are two different modules.** `ir_generator.py`
  only emits text (three-address code) — it never evaluates anything.
  `interpreter.py` is what actually runs your program and produces the
  Output tab. A lot of toy compilers skip this distinction; keeping it
  means you can swap in a real TAC-executing VM later without touching
  the interpreter that currently backs the demo.
- **The interpreter is sandboxed on purpose.** It only knows the AST node
  types defined in `ast_nodes.py`. There is no `eval()`/`exec()` of user
  input anywhere in this codebase — a MiniPy program cannot execute
  arbitrary Python.
- **Infinite-loop protection.** `interpreter.py` aborts after a step limit
  (configurable from the Settings page) rather than hanging the app on
  `while 1:`.
- **One exception class per phase** (`errors.py`) so the GUI can always
  say *which* phase failed, not just that something went wrong.

## Extending MiniPy

The four-stage pipeline (lex → parse → analyze → generate/execute) doesn't
change shape as you add features — you're adding cases to existing
`match`/`if` chains, not new architecture:

- **New operators** (`and`, `or`, `not`) — add tokens in `tokens.py` +
  `lexer.py`, a grammar rule in `parser.py`, and a case in
  `interpreter.py`'s `eval_expr`.
- **Functions** — the biggest lift: needs a `Function`/`Call` AST node, a
  call stack instead of one flat `env` dict in `interpreter.py`, and
  scope-aware entries in `symbol_table.py` (currently everything is
  `scope: "global"`).
- **Real type checking** — right now everything is `int`; a `type` field
  already exists on `SymbolEntry`, so this is about *using* it in
  `semantic.py` rather than adding new plumbing.
