# main.py
"""
Punto de entrada principal del compilador .bpp

Pipeline:
  1. Lectura del archivo fuente
  2. Análisis léxico (Lexer)
  3. Análisis sintáctico (Parser) → AST
  4. Análisis semántico Fase 1 (Checker) → tabla de símbolos
  5. (Opcional) Visualización del AST
"""

from __future__ import annotations

import sys
import argparse

from rich.console import Console
from rich.rule    import Rule
from rich         import print as rprint

from lexer    import Lexer
from parser   import parse
from checker1 import Checker
from errors   import errors, errors_detected
from ast_printer import build_rich_tree, build_graphviz

console = Console()


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="bpp",
        description="Compilador del lenguaje B++ (.bpp)",
    )
    ap.add_argument(
        "filename",
        help="Archivo fuente .bpp a compilar",
    )
    ap.add_argument(
        "--ast",
        action="store_true",
        help="Imprime el AST en la consola (Rich tree)",
    )
    ap.add_argument(
        "--graph",
        action="store_true",
        help="Genera ast.png con el AST en formato Graphviz",
    )
    ap.add_argument(
        "--symtab",
        action="store_true",
        help="Imprime la tabla de símbolos al final del análisis",
    )
    ap.add_argument(
        "--tokens",
        action="store_true",
        help="Imprime la lista de tokens antes de parsear",
    )
    return ap


# ─────────────────────────────────────────────────────────────
# Fases del compilador
# ─────────────────────────────────────────────────────────────

def phase_lex(source: str, filename: str, show_tokens: bool) -> None:
    """Fase 1: análisis léxico (solo para inspección, el parser crea su propio lexer)."""
    if not show_tokens:
        return

    console.print(Rule("[bold cyan]TOKENS[/bold cyan]"))
    lexer = Lexer()
    for tok in lexer.tokenize(source):
        console.print(f"  [dim]{tok.lineno:>4}[/dim]  [cyan]{tok.type:<20}[/cyan] {tok.value!r}")
    console.print()


def phase_parse(source: str, filename: str):
    """Fase 2: análisis sintáctico → AST."""
    console.print(Rule("[bold cyan]PARSING[/bold cyan]"))
    errors.set_source(source, filename=filename)

    try:
        ast = parse(source)
    except SyntaxError as e:
        errors.error(str(e))
        errors.print_all()
        console.print("[bold red]✖ Errores léxicos detectados. Abortando.[/bold red]\n")
        raise SystemExit(1)

    if errors_detected():
        errors.print_all()
        console.print("[bold red]✖ Errores sintácticos detectados. Abortando.[/bold red]\n")
        raise SystemExit(1)

    console.print(f"  [green]✔[/green] Archivo parseado correctamente: [bold]{filename}[/bold]\n")
    return ast


def phase_check(ast, show_symtab: bool) -> Checker:
    """Fase 3: análisis semántico (checker1)."""
    console.print(Rule("[bold cyan]ANÁLISIS SEMÁNTICO[/bold cyan]"))

    checker = Checker.check(ast)

    if checker.errors:
        for msg in checker.errors:
            # Parsear el formato "error:lineno: mensaje" del checker
            parts = msg.split(":", 2)
            if len(parts) == 3:
                try:
                    lineno = int(parts[1])
                    errors.error(parts[2].strip(), lineno=lineno)
                except ValueError:
                    errors.error(msg)
            else:
                errors.error(msg)
        errors.print_all()
        console.print(f"  [bold red]{len(checker.errors)} error(es) semántico(s) encontrado(s).[/bold red]\n")
    else:
        console.print("  [green]✔[/green] Sin errores semánticos.\n")

    if show_symtab and checker.symtab:
        console.print(Rule("[bold cyan]TABLA DE SÍMBOLOS[/bold cyan]"))
        root = checker.symtab
        while root.parent is not None:
            root = root.parent
        root.print()

    return checker


def phase_ast_print(ast) -> None:
    """Imprime el AST como árbol Rich en la consola."""
    console.print(Rule("[bold cyan]AST[/bold cyan]"))
    tree = build_rich_tree(ast)
    rprint(tree)
    console.print()


def phase_ast_graph(ast) -> None:
    """Genera ast.png con Graphviz."""
    console.print(Rule("[bold cyan]GRAPHVIZ[/bold cyan]"))
    try:
        graph = build_graphviz(ast)
        graph.render("ast", format="png", cleanup=True)
        console.print("  [green]✔[/green] Imagen generada: [bold]ast.png[/bold]\n")
    except Exception as exc:
        console.print(f"  [yellow]⚠ No se pudo generar el grafo: {exc}[/yellow]\n")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main() -> None:
    ap  = build_arg_parser()
    args = ap.parse_args()

    # ── Leer fuente ──────────────────────────────────────────
    try:
        with open(args.filename, encoding="utf-8") as fh:
            source = fh.read()
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] archivo no encontrado: '{args.filename}'")
        raise SystemExit(1)

    console.print()
    console.print(Rule(f"[bold]Compilando:[/bold] {args.filename}"))
    console.print()

    # ── Pipeline ─────────────────────────────────────────────
    phase_lex(source, args.filename, show_tokens=args.tokens)

    ast = phase_parse(source, args.filename)

    if args.ast:
        phase_ast_print(ast)

    if args.graph:
        phase_ast_graph(ast)

    checker = phase_check(ast, show_symtab=args.symtab)

    # ── Resultado final ───────────────────────────────────────
    console.print(Rule())
    if not checker.errors and not errors_detected():
        console.print("  [bold green]✔ Compilación exitosa.[/bold green]\n")
    else:
        console.print("  [bold red]✖ Compilación finalizada con errores.[/bold red]\n")
        raise SystemExit(1)


if __name__ == "__main__":
    main()