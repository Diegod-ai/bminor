# checker1.py
"""
Verificador semántico (Checker) — Fase 1.

Responsabilidades:
  - Construcción de la tabla de símbolos
  - Detección de redeclaraciones en el mismo scope
  - Verificación de símbolos no definidos
  - Verificación de que las llamadas a función apunten a funciones

Usa el patrón Visitor con despacho múltiple (multimethod/multimeta).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from multimethod import multimeta

from symtab import Symtab
from model import (
    Visitor,
    Program, Block,
    VarDecl, ConstDecl, ListDecl, FuncDecl, Param,
    Assign, PrintStmt, ReturnStmt, BreakStmt, ContinueStmt,
    IfStmt, WhileStmt, ForStmt,
    BinaryOp, UnaryOp, PostfixOp, PrefixOp,
    IntegerLiteral, FloatLiteral, BooleanLiteral,
    CharLiteral, StringLiteral,
    Variable, Call, ArrayAccess,
    SimpleType, ArrayType, FuncType,
)


# ─────────────────────────────────────────────────────────────
# Símbolo
# ─────────────────────────────────────────────────────────────

@dataclass
class Symbol:
    name:    str
    kind:    str        # 'var' | 'const' | 'param' | 'func'
    type:    Any        # nodo tipo (SimpleType, ArrayType, FuncType) o None
    node:    Any = None
    mutable: bool = True

    def __repr__(self):
        return f"Symbol(name={self.name!r}, kind={self.kind!r}, type={self.type!r})"


# ─────────────────────────────────────────────────────────────
# Checker
# ─────────────────────────────────────────────────────────────

class Checker(Visitor, metaclass=multimeta):
    """
    Recorre el AST en un único pase y construye la tabla de símbolos,
    reportando errores semánticos de nivel 1.

    Usa multimeta para despacho múltiple: cada método visit() con
    diferente anotación de tipo es una sobrecarga distinta.
    """

    def __init__(self):
        self.errors:           list[str]           = []
        self.symtab:           Optional[Symtab]    = None
        self.current_function: Optional[FuncDecl]  = None

    # ── Punto de entrada ─────────────────────────────────────

    @classmethod
    def check(cls, node) -> "Checker":
        checker = cls()
        checker._open_scope("global")
        node.accept(checker)
        return checker

    # ── Utilidades ───────────────────────────────────────────

    def _error(self, node, message: str) -> None:
        lineno = getattr(node, "lineno", "?")
        self.errors.append(f"error:{lineno}: {message}")

    def _open_scope(self, name: str) -> None:
        if self.symtab is None:
            self.symtab = Symtab(name)
        else:
            self.symtab = Symtab(name, parent=self.symtab)

    def _close_scope(self) -> None:
        if self.symtab is not None:
            self.symtab = self.symtab.parent

    def _define(self, node, name: str, symbol: Symbol) -> None:
        try:
            self.symtab.add(name, symbol)
        except Symtab.SymbolDefinedError:
            self._error(node, f"redeclaración de '{name}' en el mismo alcance")
        except Symtab.SymbolConflictError:
            self._error(node, f"conflicto de tipo para '{name}' en el mismo alcance")

    def _lookup(self, node, name: str) -> Optional[Symbol]:
        sym = self.symtab.get(name) if self.symtab else None
        if sym is None:
            self._error(node, f"símbolo '{name}' no definido")
        return sym

    def ok(self) -> bool:
        return len(self.errors) == 0

    # ── Visitor: estructuras de alto nivel ───────────────────

    def visit(self, n: Program) -> None:
        for decl in n.decls:
            decl.accept(self)

    def visit(self, n: Block) -> None:
        self._open_scope("block")
        for stmt in n.statements:
            stmt.accept(self)
        self._close_scope()

    # ── Visitor: declaraciones ───────────────────────────────

    def visit(self, n: VarDecl) -> None:
        sym = Symbol(
            name    = n.name,
            kind    = "var",
            type    = n.type,
            node    = n,
            mutable = True,
        )
        self._define(n, n.name, sym)
        if n.value is not None:
            n.value.accept(self)

    def visit(self, n: ConstDecl) -> None:
        # Visitar el valor primero para inferir el tipo
        if n.value is not None:
            n.value.accept(self)
            n.type = getattr(n.value, "type", None)
        sym = Symbol(
            name    = n.name,
            kind    = "const",
            type    = n.type,
            node    = n,
            mutable = False,
        )
        self._define(n, n.name, sym)

    def visit(self, n: ListDecl) -> None:
        sym = Symbol(
            name    = n.name,
            kind    = "var",
            type    = n.array_type,
            node    = n,
            mutable = True,
        )
        self._define(n, n.name, sym)
        if n.elements:
            for elem in n.elements:
                elem.accept(self)

    def visit(self, n: FuncDecl) -> None:
        fsym = Symbol(
            name    = n.name,
            kind    = "func",
            type    = n.func_type,
            node    = n,
            mutable = False,
        )
        self._define(n, n.name, fsym)

        prev_function         = self.current_function
        self.current_function = n

        self._open_scope(f"function {n.name}")

        if n.func_type and n.func_type.param_types:
            for param in n.func_type.param_types:
                param.accept(self)

        if n.body is not None:
            if isinstance(n.body, list):
                for stmt in n.body:
                    stmt.accept(self)
            else:
                n.body.accept(self)

        self._close_scope()
        self.current_function = prev_function

    def visit(self, n: Param) -> None:
        sym = Symbol(
            name    = n.name,
            kind    = "param",
            type    = n.type,
            node    = n,
            mutable = True,
        )
        self._define(n, n.name, sym)

    # ── Visitor: statements ──────────────────────────────────

    def visit(self, n: Assign) -> None:
        n.left.accept(self)
        n.right.accept(self)

    def visit(self, n: PrintStmt) -> None:
        if n.value:
            if isinstance(n.value, list):
                for expr in n.value:
                    expr.accept(self)
            else:
                n.value.accept(self)

    def visit(self, n: ReturnStmt) -> None:
        if n.value is not None:
            n.value.accept(self)

    def visit(self, n: BreakStmt)    -> None: pass
    def visit(self, n: ContinueStmt) -> None: pass

    def visit(self, n: IfStmt) -> None:
        n.condition.accept(self)
        n.then_branch.accept(self)
        if n.else_branch is not None:
            n.else_branch.accept(self)

    def visit(self, n: WhileStmt) -> None:
        n.condition.accept(self)
        n.body.accept(self)

    def visit(self, n: ForStmt) -> None:
        if n.init      is not None: n.init.accept(self)
        if n.condition is not None: n.condition.accept(self)
        if n.update    is not None: n.update.accept(self)
        if n.body      is not None: n.body.accept(self)

    # ── Visitor: expresiones ─────────────────────────────────

    def visit(self, n: Variable) -> None:
        sym    = self._lookup(n, n.name)
        n.sym  = sym
        n.type = sym.type if sym else None

    def visit(self, n: Call) -> None:
        sym = self._lookup(n, n.name)
        if sym is not None and sym.kind != "func":
            self._error(n, f"'{n.name}' no es una función")
        if n.args:
            for arg in n.args:
                arg.accept(self)
        n.sym  = sym
        n.type = (
            sym.type.return_type
            if sym and isinstance(sym.type, FuncType)
            else None
        )

    def visit(self, n: ArrayAccess) -> None:
        sym    = self._lookup(n, n.name)
        n.sym  = sym
        n.type = (
            sym.type.element_type
            if sym and isinstance(sym.type, ArrayType)
            else None
        )
        n.index.accept(self)

    def visit(self, n: BinaryOp)  -> None:
        n.left.accept(self)
        n.right.accept(self)

    def visit(self, n: UnaryOp)   -> None: n.expr.accept(self)
    def visit(self, n: PostfixOp) -> None: n.expr.accept(self)
    def visit(self, n: PrefixOp)  -> None: n.expr.accept(self)

    # ── Visitor: literales ───────────────────────────────────

    def visit(self, n: IntegerLiteral) -> None: n.type = SimpleType("integer")
    def visit(self, n: FloatLiteral)   -> None: n.type = SimpleType("float")
    def visit(self, n: BooleanLiteral) -> None: n.type = SimpleType("boolean")
    def visit(self, n: CharLiteral)    -> None: n.type = SimpleType("char")
    def visit(self, n: StringLiteral)  -> None: n.type = SimpleType("string")

    # ── Visitor: tipos ───────────────────────────────────────

    def visit(self, n: SimpleType) -> None: pass
    def visit(self, n: ArrayType)  -> None: pass
    def visit(self, n: FuncType)   -> None: pass