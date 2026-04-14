# errors.py
"""
Sistema de reporte de errores para el compilador.

Soporta múltiples niveles de severidad (error, warning, note),
formateo enriquecido con Rich, y resumen final al estilo compilador moderno.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from rich.console import Console
from rich.text import Text
from rich.rule import Rule
from rich.padding import Padding
from rich import print as rprint

console = Console(stderr=False)


# ─────────────────────────────────────────────
# Nivel de severidad
# ─────────────────────────────────────────────

class Level(Enum):
    NOTE    = "note"
    WARNING = "warning"
    ERROR   = "error"
    FATAL   = "fatal"

    @property
    def color(self) -> str:
        return {
            Level.NOTE:    "cyan",
            Level.WARNING: "yellow",
            Level.ERROR:   "bold red",
            Level.FATAL:   "bold white on red",
        }[self]

    @property
    def icon(self) -> str:
        return {
            Level.NOTE:    "·",
            Level.WARNING: "▲",
            Level.ERROR:   "✖",
            Level.FATAL:   "☠",
        }[self]


# ─────────────────────────────────────────────
# Entrada de diagnóstico
# ─────────────────────────────────────────────

@dataclass
class Diagnostic:
    level:    Level
    message:  str
    filename: Optional[str] = None
    lineno:   Optional[int] = None
    column:   Optional[int] = None
    source:   Optional[str] = None   # línea de fuente para mostrar contexto
    hint:     Optional[str] = None   # sugerencia opcional


# ─────────────────────────────────────────────
# Gestor principal
# ─────────────────────────────────────────────

class ErrorManager:
    """
    Gestor centralizado de diagnósticos del compilador.

    Uso básico:
        from errors import errors

        errors.error("variable no definida", lineno=5)
        errors.warning("conversión implícita", lineno=12)

        if errors.has_errors():
            raise SystemExit(1)
    """

    def __init__(self) -> None:
        self._diagnostics: list[Diagnostic] = []
        self._source_lines: dict[str, list[str]] = {}
        self.filename: Optional[str] = None

    # ── Registro de fuente ──────────────────

    def set_source(self, source: str, filename: str = "<input>") -> None:
        """Registra el código fuente para mostrar contexto en los errores."""
        self.filename = filename
        self._source_lines[filename] = source.splitlines()

    # ── API de reporte ───────────────────────

    def note(self, message: str, **kwargs) -> None:
        self._add(Level.NOTE, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self._add(Level.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self._add(Level.ERROR, message, **kwargs)

    def fatal(self, message: str, **kwargs) -> None:
        self._add(Level.FATAL, message, **kwargs)
        self.print_all()
        raise SystemExit(1)

    # ── Consultas ────────────────────────────

    def has_errors(self) -> bool:
        return any(d.level in (Level.ERROR, Level.FATAL) for d in self._diagnostics)

    def count(self, level: Optional[Level] = None) -> int:
        if level is None:
            return len(self._diagnostics)
        return sum(1 for d in self._diagnostics if d.level == level)

    def clear(self) -> None:
        self._diagnostics.clear()

    # ── Impresión ─────────────────────────────

    def print_all(self) -> None:
        """Imprime todos los diagnósticos acumulados."""
        if not self._diagnostics:
            return
        console.print()
        for diag in self._diagnostics:
            self._render(diag)
        self._render_summary()

    def _add(
        self,
        level: Level,
        message: str,
        lineno: Optional[int]   = None,
        column: Optional[int]   = None,
        filename: Optional[str] = None,
        hint: Optional[str]     = None,
    ) -> None:
        fname = filename or self.filename

        # Obtener línea de fuente si está disponible
        source_line = None
        if fname and fname in self._source_lines and lineno:
            lines = self._source_lines[fname]
            if 1 <= lineno <= len(lines):
                source_line = lines[lineno - 1]

        diag = Diagnostic(
            level=level,
            message=message,
            filename=fname,
            lineno=lineno,
            column=column,
            source=source_line,
            hint=hint,
        )
        self._diagnostics.append(diag)

    def _render(self, diag: Diagnostic) -> None:
        """Renderiza un diagnóstico individual al estilo clang/rustc."""

        # ── Encabezado: severidad + mensaje ──
        label = Text()
        label.append(f" {diag.level.icon} {diag.level.value} ", style=diag.level.color)
        label.append(f" {diag.message}", style="bold white")
        console.print(label)

        # ── Ubicación ─────────────────────────
        if diag.filename or diag.lineno:
            loc_parts = []
            if diag.filename:
                loc_parts.append(diag.filename)
            if diag.lineno:
                loc_parts.append(str(diag.lineno))
            if diag.column:
                loc_parts.append(str(diag.column))
            loc = ":".join(loc_parts)
            console.print(f"   [dim]╰─ {loc}[/dim]")

        # ── Contexto de fuente ─────────────────
        if diag.source and diag.lineno:
            lineno_str = str(diag.lineno)
            pad = " " * len(lineno_str)

            console.print(f"   [dim]{pad} │[/dim]")
            console.print(f"   [dim]{lineno_str} │[/dim]  {diag.source}")

            # Subrayado en la columna si está disponible
            if diag.column:
                col = diag.column - 1
                underline = " " * col + "^"
                console.print(
                    f"   [dim]{pad} │[/dim]  [{diag.level.color}]{underline}[/{diag.level.color}]"
                )

            console.print(f"   [dim]{pad} │[/dim]")

        # ── Hint ──────────────────────────────
        if diag.hint:
            console.print(f"   [cyan]hint:[/cyan] {diag.hint}")

        console.print()

    def _render_summary(self) -> None:
        """Imprime el resumen final al estilo compilador."""
        errors   = self.count(Level.ERROR) + self.count(Level.FATAL)
        warnings = self.count(Level.WARNING)

        if errors == 0 and warnings == 0:
            return

        console.print(Rule(style="dim"))

        summary = Text("  Compilación finalizada con ")
        if errors:
            summary.append(f"{errors} error{'es' if errors != 1 else ''}", style="bold red")
        if errors and warnings:
            summary.append(" y ")
        if warnings:
            summary.append(f"{warnings} advertencia{'s' if warnings != 1 else ''}", style="bold yellow")
        summary.append(".")

        console.print(summary)
        console.print()


# ─────────────────────────────────────────────
# Instancia global (interfaz principal)
# ─────────────────────────────────────────────

errors = ErrorManager()


# ─────────────────────────────────────────────
# API funcional compatible con código anterior
# ─────────────────────────────────────────────

def error(message: str, lineno: Optional[int] = None, **kwargs) -> None:
    """Compatibilidad con la API original: error(message, lineno)."""
    errors.error(message, lineno=lineno, **kwargs)

def warning(message: str, lineno: Optional[int] = None, **kwargs) -> None:
    errors.warning(message, lineno=lineno, **kwargs)

def note(message: str, lineno: Optional[int] = None, **kwargs) -> None:
    errors.note(message, lineno=lineno, **kwargs)

def errors_detected() -> int:
    """Compatibilidad con la API original."""
    return errors.count(Level.ERROR) + errors.count(Level.FATAL)

def clear_errors() -> None:
    """Compatibilidad con la API original."""
    errors.clear()


# ─────────────────────────────────────────────
# Demo / prueba rápida
# ─────────────────────────────────────────────

if __name__ == "__main__":
    SOURCE = """\
function main : integer() {
    x : integer = 10;
    y : undefined_type;
    return x + z;
}"""

    errors.set_source(SOURCE, filename="main.bpp")

    errors.error(
        "tipo 'undefined_type' no está definido",
        lineno=3, column=9,
        hint="¿Quisiste decir 'integer' o 'float'?",
    )
    errors.error(
        "símbolo 'z' no definido",
        lineno=4, column=16,
    )
    errors.warning(
        "variable 'y' declarada pero nunca usada",
        lineno=3,
    )
    errors.note(
        "considera usar 'integer' para valores enteros",
        lineno=3,
    )

    errors.print_all()