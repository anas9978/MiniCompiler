"""
app.py
------
Streamlit front-end for the MiniPy Compiler. This file only does
UI wiring: it calls into lexer.py / parser.py / semantic.py /
ir_generator.py / interpreter.py and renders their results. No
compiler logic lives here.
"""

import time
from pathlib import Path

import streamlit as st

from lexer import tokenize
from parser import parse
from semantic import analyze
from ir_generator import generate_tac
from interpreter import interpret
from errors import LexError, ParserError, InterpreterError

EXAMPLES_DIR = Path(__file__).parent / "examples"

st.set_page_config(
    page_title="MiniPy Compiler",
    page_icon="🐍",
    layout="wide",
)

# ---------------------------------------------------------------
# Custom CSS: monospace editor feel + tighter card styling.
# Colors intentionally echo the .streamlit/config.toml dark theme
# rather than fighting it.
# ---------------------------------------------------------------
st.markdown("""
<style>
textarea, code, pre { font-family: 'SFMono-Regular', Consolas, Menlo, monospace !important; }
div[data-testid="stMetricValue"] { font-size: 1.4rem; }
.mpy-banner {
    padding: 0.7rem 1rem;
    border-radius: 8px;
    font-weight: 500;
    margin-bottom: 0.8rem;
}
.mpy-banner-success { background: #113322; color: #6ee7a0; border: 1px solid #1c5c38; }
.mpy-banner-error { background: #3a1620; color: #fb9aa5; border: 1px solid #6a2530; }
.token-badge {
    display: inline-block; padding: 1px 8px; border-radius: 5px;
    font-size: 0.75rem; font-weight: 600; font-family: monospace;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# Session state
# ---------------------------------------------------------------
if "source_code" not in st.session_state:
    st.session_state.source_code = (EXAMPLES_DIR / "example.mpy").read_text()
if "filename" not in st.session_state:
    st.session_state.filename = "example.mpy"
if "max_steps" not in st.session_state:
    st.session_state.max_steps = 200_000
if "result" not in st.session_state:
    st.session_state.result = None

PAGES = ["Compiler", "Examples"]

with st.sidebar:
    st.markdown("## 🐍 MiniPy Compiler")
    st.caption("A visual Python-like language compiler")
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")


# ---------------------------------------------------------------
# Compiler pipeline (pure function: source -> result dict)
# ---------------------------------------------------------------
def run_pipeline(source: str, max_steps: int) -> dict:
    result = {
        "status": "success",
        "phase": None,
        "message": "Compilation successful!",
        "tokens": [],
        "ast": None,
        "symbol_table": [],
        "semantic_errors": [],
        "tac": [],
        "output": [],
        "output_error": None,
        "token_count": 0,
        "elapsed_ms": 0.0,
    }
    start = time.perf_counter()

    try:
        tokens = tokenize(source)
    except LexError as e:
        result["status"] = "error"
        result["phase"] = e.phase
        result["message"] = f"Lexical error (line {e.line}): {e.message}"
        result["elapsed_ms"] = (time.perf_counter() - start) * 1000
        return result

    result["tokens"] = tokens
    result["token_count"] = len([t for t in tokens if t.type.name != "NEWLINE"])

    try:
        ast = parse(tokens)
    except ParserError as e:
        result["status"] = "error"
        result["phase"] = e.phase
        result["message"] = f"Syntax error (line {e.line}): {e.message}"
        result["elapsed_ms"] = (time.perf_counter() - start) * 1000
        return result

    result["ast"] = ast

    semantic_result = analyze(ast)
    result["symbol_table"] = semantic_result.symbol_table.entries()
    result["semantic_errors"] = semantic_result.errors

    result["tac"] = generate_tac(ast)

    if semantic_result.errors:
        result["status"] = "error"
        result["phase"] = "Semantic Analysis"
        result["message"] = f"Compilation failed: {len(semantic_result.errors)} semantic error(s) found"
        result["elapsed_ms"] = (time.perf_counter() - start) * 1000
        return result

    try:
        result["output"] = interpret(ast, max_steps=max_steps)
    except InterpreterError as e:
        result["status"] = "error"
        result["phase"] = e.phase
        result["message"] = f"Runtime error (line {e.line}): {e.message}"
        result["output_error"] = e.message

    result["elapsed_ms"] = (time.perf_counter() - start) * 1000
    return result


def banner(status: str, message: str):
    cls = "mpy-banner-success" if status == "success" else "mpy-banner-error"
    st.markdown(f'<div class="mpy-banner {cls}">{message}</div>', unsafe_allow_html=True)


TOKEN_COLORS = {
    "IDENTIFIER": "#1e3a5f;color:#7dd3fc",
    "NUMBER": "#113a33;color:#2dd4bf",
    "IF": "#33204d;color:#a78bfa", "ELSE": "#33204d;color:#a78bfa",
    "WHILE": "#33204d;color:#a78bfa", "PRINT": "#33204d;color:#a78bfa",
}
DEFAULT_TOKEN_COLOR = "#202b3f;color:#8698b8"


def render_ast_node(node, label_override=None) -> str:
    """Render one AST node (and children) as nested markdown bullets."""
    kind = type(node).__name__
    lines = []

    def label(n, override=None):
        if override:
            return override
        t = type(n).__name__
        if t == "Assign":
            return f"**Assign**({n.name})"
        if t == "BinaryOp":
            return f"**BinaryOp**({n.op})"
        if t == "UnaryOp":
            return f"**UnaryOp**({n.op})"
        if t == "Identifier":
            return f"**Identifier**({n.name})"
        if t == "Number":
            return f"**Number**({n.value})"
        return f"**{t}**"

    def walk(n, depth, override=None):
        indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * depth
        lines.append(f"{indent}- {label(n, override)}")
        t = type(n).__name__
        if t == "Program":
            for c in n.body:
                walk(c, depth + 1)
        elif t == "Assign":
            walk(n.expr, depth + 1)
        elif t == "If":
            walk(n.cond, depth + 1, "Condition")
            lines.append(f"{'&nbsp;&nbsp;&nbsp;&nbsp;' * (depth + 1)}- **Then**")
            for c in n.then_block:
                walk(c, depth + 2)
            if n.else_block:
                lines.append(f"{'&nbsp;&nbsp;&nbsp;&nbsp;' * (depth + 1)}- **Else**")
                for c in n.else_block:
                    walk(c, depth + 2)
        elif t == "While":
            walk(n.cond, depth + 1, "Condition")
            lines.append(f"{'&nbsp;&nbsp;&nbsp;&nbsp;' * (depth + 1)}- **Body**")
            for c in n.body:
                walk(c, depth + 2)
        elif t == "Print":
            walk(n.expr, depth + 1)
        elif t == "BinaryOp":
            walk(n.left, depth + 1)
            walk(n.right, depth + 1)
        elif t == "UnaryOp":
            walk(n.expr, depth + 1)

    walk(node, 0, label_override)
    return "\n".join(lines)


# =================================================================
# PAGE: Compiler
# =================================================================
if page == "Compiler":
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader("📄 Source Code")
        st.caption(f"`{st.session_state.filename}`")

        st.session_state.source_code = st.text_area(
            "Source code editor",
            value=st.session_state.source_code,
            height=380,
            label_visibility="collapsed",
        )

        col_a, col_b, col_c, col_d = st.columns(4)
        compile_clicked = col_a.button("▶ Compile & Run", type="primary", use_container_width=True)
        

       
        

        if compile_clicked:
            st.session_state.result = run_pipeline(st.session_state.source_code, st.session_state.max_steps)

        result = st.session_state.result
        if result:
            banner(result["status"], result["message"])
            m1, m2, m3 = st.columns(3)
            m1.metric("Tokens", result["token_count"])
            m2.metric("Symbols", len(result["symbol_table"]))
            m3.metric("Time", f"{result['elapsed_ms']:.2f} ms")

    with right:
        st.subheader("🧩 Compiler Phases")
        result = st.session_state.result

        if not result:
            st.info("Click **Compile & Run** to see tokens, AST, semantic analysis, TAC, and output here.")
        else:
            tabs = st.tabs(["Tokens", "AST", "Semantic", "3-Address Code", "Output"])

            # --- Tokens ---
            with tabs[0]:
                if result["tokens"]:
                    rows = [
                        {"#": i + 1, "Token Type": t.type.name, "Value": t.value, "Line": t.line, "Column": t.col}
                        for i, t in enumerate(result["tokens"])
                        if t.type.name != "NEWLINE"
                    ]
                    st.dataframe(rows, use_container_width=True, height=320, hide_index=True)
                else:
                    st.caption("No tokens (lexical error before any tokens were produced).")

            # --- AST ---
            with tabs[1]:
                if result["ast"]:
                    st.markdown(render_ast_node(result["ast"]), unsafe_allow_html=True)
                else:
                    st.caption("No AST (parsing failed).")

            # --- Semantic ---
            with tabs[2]:
                if result["semantic_errors"]:
                    banner("error", f"{len(result['semantic_errors'])} semantic error(s) found")
                else:
                    banner("success", "No semantic errors found!")

                st.markdown("**Symbol Table**")
                if result["symbol_table"]:
                    st.dataframe(
                        [{"Name": s.name, "Type": s.type, "Scope": s.scope, "Line": s.line} for s in result["symbol_table"]],
                        use_container_width=True, hide_index=True,
                    )
                else:
                    st.caption("No symbols declared yet.")

                if result["semantic_errors"]:
                    st.markdown("**Errors**")
                    for e in result["semantic_errors"]:
                        banner("error", f"Line {e['line']}: {e['message']}")

            # --- TAC ---
            with tabs[3]:
                if result["tac"]:
                    tac_text = "\n".join(f"{i + 1:>3}  {line}" for i, line in enumerate(result["tac"]))
                    st.code(tac_text, language=None)
                   
                else:
                    st.caption("No TAC generated (parsing failed).")

            # --- Output ---
            with tabs[4]:
                out_text = "\n".join(result["output"])
                if result["output_error"]:
                    out_text += ("\n" if result["output"] else "") + f"--- runtime error: {result['message']} ---"
                    st.code(out_text or "(no output)", language=None)
                elif result["status"] == "success":
                    out_text += ("\n" if result["output"] else "") + "\n---------------------------\nProcess completed successfully!"
                    st.code(out_text, language=None)
                else:
                    st.caption("Execution skipped due to earlier compiler errors.")

            report_lines = [
                f"MiniPy Compilation Report — {st.session_state.filename}",
                f"Status: {result['status']}",
                f"Message: {result['message']}",
                f"Tokens: {result['token_count']}  |  Symbols: {len(result['symbol_table'])}  |  Time: {result['elapsed_ms']:.2f} ms",
                "",
                "--- Output ---",
                *result["output"],
            ]
           

# =================================================================
# PAGE: Examples
# =================================================================
elif page == "Examples":
    st.subheader("📚 Sample Programs")
    st.caption("Pick one to load it into the Compiler editor.")

    example_descriptions = {
        "example.mpy": "Arithmetic, if/else, and a while loop — matches the walkthrough in the docs.",
        "loops_and_conditions.mpy": "A while loop with a nested if/else and the modulo operator.",
        "semantic_error.mpy": "Intentionally broken: uses two variables before they're ever assigned.",
    }

    for file in sorted(EXAMPLES_DIR.glob("*.mpy")):
        with st.expander(f"📄 {file.name}"):
            code = file.read_text()
            st.caption(example_descriptions.get(file.name, ""))
            st.code(code, language="python")
            if st.button(f"Load {file.name}", key=f"load_{file.name}"):
                st.session_state.source_code = code
                st.session_state.filename = file.name
                st.session_state.result = None
                st.success(f"Loaded {file.name} — switch to the Compiler page to run it.")



