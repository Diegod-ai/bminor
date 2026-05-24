from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from multimethod import multimeta

from model import (
    # Programa
    Program,
    # Declaraciones
    VarDecl, ConstDecl, ListDecl, FuncDecl, Param,
    # Tipos
    SimpleType, ArrayType, FuncType,
    # Sentencias
    Block, Assign, PrintStmt, ReturnStmt,
    IfStmt, WhileStmt, ForStmt, BreakStmt, ContinueStmt,
    # Expresiones
    BinaryOp, UnaryOp, PostfixOp, PrefixOp,
    Variable, ArrayAccess, Call,
    # Literales
    IntegerLiteral, FloatLiteral, BooleanLiteral, CharLiteral, StringLiteral,
)


# ===================================================
# Modelo IR
# ===================================================

Instruction = tuple


@dataclass
class Storage:
    """Describe dónde vive un símbolo durante la generación de IR."""
    name: str
    ty: object          # SimpleType | FuncType | str
    is_global: bool = False
    is_param: bool = False
    is_const: bool = False


@dataclass
class IRFunction:
    name: str
    params: list[tuple[str, object]]
    return_type: object
    instructions: list[Instruction] = field(default_factory=list)


@dataclass
class IRProgram:
    globals: list[Instruction] = field(default_factory=list)
    functions: list[IRFunction] = field(default_factory=list)

    def format(self) -> str:
        out: list[str] = []
        if self.globals:
            out.append("# Globals")
            for inst in self.globals:
                out.append(format_instruction(inst))
            out.append("")
        for fn in self.functions:
            params = ", ".join(f"{name}:{ty}" for name, ty in fn.params)
            out.append(f"function {fn.name}({params}) -> {fn.return_type}")
            for inst in fn.instructions:
                out.append(f"  {format_instruction(inst)}")
            out.append("")
        return "\n".join(out).rstrip()


def format_instruction(inst: Instruction) -> str:
    op = inst[0]
    if len(inst) == 1:
        return op
    args = ", ".join(
        repr(x) if isinstance(x, str) and x.startswith("L") else str(x)
        for x in inst[1:]
    )
    return f"{op} {args}"


# ===================================================
# Generador de Representación Intermedia (IR)
# ===================================================

class IRCodeGen(metaclass=multimeta):
    """
    Visitor que recorre el AST y produce instrucciones SSA de 3 direcciones.

    Uso:
        ir = IRCodeGen.generate(ast)
        print(ir.format())
    """

    def __init__(self):
        self.program = IRProgram()
        self.current_function: Optional[IRFunction] = None
        self.current_return_type = None
        self.temp_count = 0
        self.label_count = 0
        self.scopes: list[dict[str, Storage]] = []
        # Para strings: mapa de valor -> nombre de dato global
        self._string_data: dict[str, str] = {}
        self._string_count = 0
        # Stack de labels para break/continue
        self._loop_end_stack: list[str] = []
        self._loop_test_stack: list[str] = []

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------

    @classmethod
    def generate(cls, node: Program) -> IRProgram:
        gen = cls()
        gen.visit(node)
        return gen.program

    # ------------------------------------------------------------------
    # Helpers: temporales y labels
    # ------------------------------------------------------------------

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"R{self.temp_count}"

    def new_label(self, prefix: str = "L") -> str:
        self.label_count += 1
        return f"{prefix}{self.label_count}"

    def emit(self, *inst) -> None:
        t = tuple(inst)
        if self.current_function is None:
            self.program.globals.append(t)
        else:
            self.current_function.instructions.append(t)

    # ------------------------------------------------------------------
    # Helpers: scopes y símbolos
    # ------------------------------------------------------------------

    def push_scope(self) -> None:
        self.scopes.append({})

    def pop_scope(self) -> None:
        self.scopes.pop()

    def bind(self, storage: Storage) -> None:
        if not self.scopes:
            self.push_scope()
        self.scopes[-1][storage.name] = storage

    def lookup(self, name: str) -> Storage:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise NameError(f"IRCodeGen: símbolo no resuelto '{name}'")

    # ------------------------------------------------------------------
    # Helpers: tipos → sufijos de opcode
    # ------------------------------------------------------------------

    _SUFFIX_MAP = {
        'integer':  'I',
        'boolean':  'I',   # booleanos se representan como int 0/1
        'float':    'F',
        'char':     'B',
        'string':   'S',
        'void':     'V',
    }

    def _type_name(self, ty) -> str:
        """Extrae el nombre de tipo como string ('integer', 'float', …)."""
        if isinstance(ty, SimpleType):
            return ty.name
        if isinstance(ty, str):
            return ty
        return 'integer'

    def _suffix(self, ty) -> str:
        return self._SUFFIX_MAP.get(self._type_name(ty), 'I')

    def _infer_type(self, node) -> str:
        """Infiere el tipo de un nodo expresión (devuelve nombre string)."""
        # 1. El checker puede haber anotado .type
        ty = getattr(node, 'type', None)
        if ty is not None:
            return self._type_name(ty)
        # 2. Casos concretos de literales
        if isinstance(node, IntegerLiteral):
            return 'integer'
        if isinstance(node, FloatLiteral):
            return 'float'
        if isinstance(node, BooleanLiteral):
            return 'boolean'
        if isinstance(node, CharLiteral):
            return 'char'
        if isinstance(node, StringLiteral):
            return 'string'
        # 3. Variable: buscar en scopes
        if isinstance(node, Variable):
            try:
                st = self.lookup(node.name)
                return self._type_name(st.ty)
            except NameError:
                pass
        return 'integer'

    def _infer_type_from_literal(self, node) -> SimpleType:
        """Devuelve SimpleType para constantes."""
        mapping = {
            IntegerLiteral: 'integer',
            FloatLiteral:   'float',
            BooleanLiteral: 'boolean',
            CharLiteral:    'char',
            StringLiteral:  'string',
        }
        return SimpleType(mapping.get(type(node), 'integer'))

    # ------------------------------------------------------------------
    # Helpers: strings → DATAS globales
    # ------------------------------------------------------------------

    def _intern_string(self, value: str) -> str:
        """Registra un string literal como bloque DATAS global y devuelve su nombre."""
        if value in self._string_data:
            return self._string_data[value]
        self._string_count += 1
        label = f"_str{self._string_count}"
        self._string_data[value] = label
        bytes_values = [ord(c) for c in value] + [0]  # null-terminated
        self.program.globals.append(("DATAS", label, *bytes_values))
        return label

    # ------------------------------------------------------------------
    # Programa
    # ------------------------------------------------------------------

    def visit(self, node: Program):
        self.push_scope()

        # Primera pasada: registrar nombres globales
        for decl in node.decls:
            if isinstance(decl, VarDecl):
                self.bind(Storage(decl.name, decl.type, is_global=True))
            elif isinstance(decl, ConstDecl):
                inferred = self._infer_type_from_literal(decl.value)
                self.bind(Storage(decl.name, inferred, is_global=True, is_const=True))
            elif isinstance(decl, ListDecl):
                self.bind(Storage(decl.name, decl.array_type, is_global=True))
            elif isinstance(decl, FuncDecl):
                self.bind(Storage(decl.name, decl.func_type, is_global=True))

        # Segunda pasada: generar IR
        for decl in node.decls:
            self.visit(decl)

        self.pop_scope()
        return self.program

    # ------------------------------------------------------------------
    # Declaraciones
    # ------------------------------------------------------------------

    def visit(self, node: VarDecl):
        sfx = self._suffix(node.type)

        if self.current_function is None:
            # Variable global
            self.emit(f"VAR{sfx}", node.name)
            if node.value is not None:
                src = self.visit(node.value)
                self.emit(f"STORE{sfx}", src, node.name)
        else:
            # Variable local
            self.bind(Storage(node.name, node.type))
            self.emit(f"ALLOC{sfx}", node.name)
            if node.value is not None:
                src = self.visit(node.value)
                self.emit(f"STORE{sfx}", src, node.name)

    def visit(self, node: ConstDecl):
        inferred = self._infer_type_from_literal(node.value)
        sfx = self._suffix(inferred)

        if self.current_function is None:
            self.emit(f"VAR{sfx}", node.name)
            src = self.visit(node.value)
            self.emit(f"STORE{sfx}", src, node.name)
        else:
            self.bind(Storage(node.name, inferred, is_const=True))
            self.emit(f"ALLOC{sfx}", node.name)
            src = self.visit(node.value)
            self.emit(f"STORE{sfx}", src, node.name)

    def visit(self, node: ListDecl):
        """Declaración de arreglo con elementos opcionales."""
        elem_ty = getattr(node.array_type, 'element_type', SimpleType('integer'))
        sfx = self._suffix(elem_ty)
        self.bind(Storage(node.name, node.array_type,
                          is_global=(self.current_function is None)))
        if self.current_function is None:
            self.emit(f"VAR{sfx}", node.name)
        else:
            self.emit(f"ALLOC{sfx}", node.name)

        if node.elements:
            for i, elem in enumerate(node.elements):
                src = self.visit(elem)
                self.emit(f"STORE{sfx}", src, f"{node.name}[{i}]")

    def visit(self, node: FuncDecl):
        prev_fn = self.current_function
        prev_ret = self.current_return_type

        # FuncType contiene return_type y param_types (lista[Param])
        func_type: FuncType = node.func_type
        ret_type = func_type.return_type
        params_list = func_type.param_types or []

        fn = IRFunction(
            name=node.name,
            params=[(p.name, p.type) for p in params_list],
            return_type=ret_type,
        )
        self.program.functions.append(fn)
        self.current_function = fn
        self.current_return_type = ret_type

        self.push_scope()

        # Registrar parámetros y reservar espacio
        for p in params_list:
            self.bind(Storage(p.name, p.type, is_param=True))
            self.emit(f"ALLOC{self._suffix(p.type)}", p.name)

        # Generar cuerpo
        body = node.body
        if body is not None:
            if isinstance(body, list):
                for stmt in body:
                    self.visit(stmt)
            else:
                self.visit(body)

        # Para funciones void: emitir RET implícito si falta
        if isinstance(ret_type, SimpleType) and ret_type.name == 'void':
            instrs = fn.instructions
            if not instrs or instrs[-1][0] != "RET":
                self.emit("RET")

        self.pop_scope()
        self.current_function = prev_fn
        self.current_return_type = prev_ret

    def visit(self, node: Param):
        return None

    # ------------------------------------------------------------------
    # Sentencias
    # ------------------------------------------------------------------

    def visit(self, node: Block):
        self.push_scope()
        for stmt in node.statements:
            self.visit(stmt)
        self.pop_scope()

    def visit(self, node: Assign):
        """
        Soporta:
          x = expr
          x += expr  x -= expr  x *= expr  x /= expr
          arr[i] = expr
        """
        op = node.op

        if isinstance(node.left, Variable):
            var_name = node.left.name
            storage = self.lookup(var_name)
            ty = self._type_name(storage.ty)
            sfx = self._suffix(ty)

            if op == '=':
                src = self.visit(node.right)
                self.emit(f"STORE{sfx}", src, var_name)
            else:
                # Operador compuesto: cargar, operar, guardar
                left_reg = self.new_temp()
                self.emit(f"LOAD{sfx}", var_name, left_reg)
                right_reg = self.visit(node.right)
                out = self.new_temp()
                base = op[:-1]  # eliminar '='
                arith = {
                    '+': f"ADD{sfx}", '-': f"SUB{sfx}",
                    '*': f"MUL{sfx}", '/': f"DIV{sfx}",
                }
                opcode = arith.get(base, f"ADD{sfx}")
                self.emit(opcode, left_reg, right_reg, out)
                self.emit(f"STORE{sfx}", out, var_name)

        elif isinstance(node.left, ArrayAccess):
            # arr[i] = expr
            arr_name = node.left.name
            idx_reg = self.visit(node.left.index)
            src = self.visit(node.right)
            self.emit("STOREI", src, f"{arr_name}[{idx_reg}]")

        else:
            raise NotImplementedError(
                f"Assign: destino no soportado {type(node.left).__name__}"
            )

    def visit(self, node: PrintStmt):
        val = node.value
        if val is None:
            return
        # value puede ser lista o expresión única
        items = val if isinstance(val, list) else [val]
        for expr in items:
            reg = self.visit(expr)
            ty = self._infer_type(expr)
            sfx = self._suffix(ty)
            if ty == 'string':
                self.emit("PRINTS", reg)
            else:
                self.emit(f"PRINT{sfx}", reg)

    def visit(self, node: ReturnStmt):
        if node.value is None:
            self.emit("RET")
        else:
            reg = self.visit(node.value)
            self.emit("RET", reg)

    def visit(self, node: IfStmt):
        test_reg = self.visit(node.condition)

        if node.else_branch is not None:
            label_then = self.new_label("Lthen")
            label_else = self.new_label("Lelse")
            label_end  = self.new_label("Lend")

            self.emit("CBRANCH", test_reg, label_then, label_else)
            self.emit("LABEL",   label_then)
            self.visit(node.then_branch)
            self.emit("BRANCH",  label_end)
            self.emit("LABEL",   label_else)
            self.visit(node.else_branch)
            self.emit("LABEL",   label_end)
        else:
            label_then = self.new_label("Lthen")
            label_end  = self.new_label("Lend")

            self.emit("CBRANCH", test_reg, label_then, label_end)
            self.emit("LABEL",   label_then)
            self.visit(node.then_branch)
            self.emit("LABEL",   label_end)

    def visit(self, node: WhileStmt):
        label_test = self.new_label("Ltest")
        label_body = self.new_label("Lbody")
        label_end  = self.new_label("Lend")

        self._loop_test_stack.append(label_test)
        self._loop_end_stack.append(label_end)
        try:
            self.emit("LABEL",   label_test)
            test_reg = self.visit(node.condition)
            self.emit("CBRANCH", test_reg, label_body, label_end)
            self.emit("LABEL",   label_body)
            self.visit(node.body)
            self.emit("BRANCH",  label_test)
            self.emit("LABEL",   label_end)
        finally:
            self._loop_test_stack.pop()
            self._loop_end_stack.pop()

    def visit(self, node: ForStmt):
        if node.init is not None:
            self.visit(node.init)

        label_test = self.new_label("Ltest")
        label_body = self.new_label("Lbody")
        label_end  = self.new_label("Lend")

        self._loop_test_stack.append(label_test)
        self._loop_end_stack.append(label_end)
        try:
            self.emit("LABEL", label_test)
            if node.condition is not None:
                test_reg = self.visit(node.condition)
                self.emit("CBRANCH", test_reg, label_body, label_end)
            self.emit("LABEL", label_body)
            self.visit(node.body)
            if node.update is not None:
                self.visit(node.update)
            self.emit("BRANCH", label_test)
            self.emit("LABEL",  label_end)
        finally:
            self._loop_test_stack.pop()
            self._loop_end_stack.pop()

    def visit(self, node: BreakStmt):
        if self._loop_end_stack:
            self.emit("BRANCH", self._loop_end_stack[-1])

    def visit(self, node: ContinueStmt):
        if self._loop_test_stack:
            self.emit("BRANCH", self._loop_test_stack[-1])

    # ------------------------------------------------------------------
    # Expresiones
    # ------------------------------------------------------------------

    def visit(self, node: Variable):
        storage = self.lookup(node.name)
        ty = self._type_name(storage.ty)
        sfx = self._suffix(ty)
        tmp = self.new_temp()
        self.emit(f"LOAD{sfx}", node.name, tmp)
        # Anotar tipo para _infer_type posterior
        node.type = storage.ty
        return tmp

    def visit(self, node: ArrayAccess):
        idx_reg = self.visit(node.index)
        tmp = self.new_temp()
        self.emit("LOADI", f"{node.name}[{idx_reg}]", tmp)
        return tmp

    def visit(self, node: Call):
        args = node.args or []
        arg_regs = [self.visit(a) for a in args]
        tmp = self.new_temp()
        self.emit("CALL", node.name, *arg_regs, tmp)
        return tmp

    def visit(self, node: BinaryOp):
        op = node.op

        # ----- Cortocircuito: && -----
        if op == '&&':
            return self._and_short_circuit(node)

        # ----- Cortocircuito: || -----
        if op == '||':
            return self._or_short_circuit(node)

        left_reg  = self.visit(node.left)
        right_reg = self.visit(node.right)
        ty  = self._infer_type(node.left)
        sfx = self._suffix(ty)
        out = self.new_temp()

        # Aritmética
        arith = {
            '+': f"ADD{sfx}", '-': f"SUB{sfx}",
            '*': f"MUL{sfx}", '/': f"DIV{sfx}",
        }
        if op in arith:
            self.emit(arith[op], left_reg, right_reg, out)
            return out

        # Comparaciones
        if op in {'==', '!=', '<', '<=', '>', '>='}:
            self.emit(f"CMP{sfx}", op, left_reg, right_reg, out)
            return out

        # Bitwise
        bitwise = {'&': 'AND', '|': 'OR', '^': 'XOR'}
        if op in bitwise:
            self.emit(bitwise[op], left_reg, right_reg, out)
            return out

        raise NotImplementedError(f"BinaryOp: operador no soportado '{op}'")

    def _and_short_circuit(self, node: BinaryOp) -> str:
        """
        &&: si left == 0  →  resultado = 0
            si left != 0  →  resultado = (right != 0)
        """
        result_var = f"__and_{self.new_temp()}"
        self.emit("ALLOCI", result_var)

        label_right = self.new_label("Land_right")
        label_false = self.new_label("Land_false")
        label_end   = self.new_label("Land_end")

        left_reg = self.visit(node.left)
        self.emit("CBRANCH", left_reg, label_right, label_false)

        # Rama: evaluar derecho
        self.emit("LABEL", label_right)
        right_reg = self.visit(node.right)
        self.emit("STOREI", right_reg, result_var)
        self.emit("BRANCH", label_end)

        # Rama: false (left era 0)
        self.emit("LABEL", label_false)
        tmp_zero = self.new_temp()
        self.emit("MOVI", 0, tmp_zero)
        self.emit("STOREI", tmp_zero, result_var)

        self.emit("LABEL", label_end)
        out = self.new_temp()
        self.emit("LOADI", result_var, out)
        return out

    def _or_short_circuit(self, node: BinaryOp) -> str:
        """
        ||: si left != 0  →  resultado = 1
            si left == 0  →  resultado = (right != 0)
        """
        result_var = f"__or_{self.new_temp()}"
        self.emit("ALLOCI", result_var)

        label_right = self.new_label("Lor_right")
        label_true  = self.new_label("Lor_true")
        label_end   = self.new_label("Lor_end")

        left_reg = self.visit(node.left)
        self.emit("CBRANCH", left_reg, label_true, label_right)

        # Rama: evaluar derecho
        self.emit("LABEL", label_right)
        right_reg = self.visit(node.right)
        self.emit("STOREI", right_reg, result_var)
        self.emit("BRANCH", label_end)

        # Rama: true (left ya era verdadero)
        self.emit("LABEL", label_true)
        tmp_one = self.new_temp()
        self.emit("MOVI", 1, tmp_one)
        self.emit("STOREI", tmp_one, result_var)

        self.emit("LABEL", label_end)
        out = self.new_temp()
        self.emit("LOADI", result_var, out)
        return out

    def visit(self, node: UnaryOp):
        """Operadores unarios: +  -  !"""
        operand_reg = self.visit(node.expr)
        ty  = self._infer_type(node.expr)
        sfx = self._suffix(ty)
        out = self.new_temp()
        op  = node.op

        if op == '+':
            # Identidad: copiar sumando cero
            zero = self.new_temp()
            self.emit(f"MOV{sfx}", 0, zero)
            self.emit(f"ADD{sfx}", zero, operand_reg, out)
        elif op == '-':
            # Negación: 0 - operand
            zero = self.new_temp()
            self.emit(f"MOV{sfx}", 0, zero)
            self.emit(f"SUB{sfx}", zero, operand_reg, out)
        elif op == '!':
            # NOT lógico: comparar == 0
            zero = self.new_temp()
            self.emit("MOVI", 0, zero)
            self.emit("CMPI", "==", operand_reg, zero, out)
        else:
            raise NotImplementedError(f"UnaryOp: operador no soportado '{op}'")
        return out

    def visit(self, node: PostfixOp):
        """
        x++  x--
        Devuelve el valor *antes* del incremento/decremento.
        """
        inner = node.expr
        if not isinstance(inner, Variable):
            raise NotImplementedError("PostfixOp solo soporta variables simples")

        storage = self.lookup(inner.name)
        ty  = self._type_name(storage.ty)
        sfx = self._suffix(ty)

        old_val = self.new_temp()
        self.emit(f"LOAD{sfx}", inner.name, old_val)

        one = self.new_temp()
        self.emit(f"MOV{sfx}", 1, one)
        new_val = self.new_temp()

        if node.op == '++':
            self.emit(f"ADD{sfx}", old_val, one, new_val)
        else:
            self.emit(f"SUB{sfx}", old_val, one, new_val)

        self.emit(f"STORE{sfx}", new_val, inner.name)
        return old_val   # valor previo al cambio

    def visit(self, node: PrefixOp):
        """
        ++x  --x
        Devuelve el valor *después* del incremento/decremento.
        """
        inner = node.expr
        if not isinstance(inner, Variable):
            raise NotImplementedError("PrefixOp solo soporta variables simples")

        storage = self.lookup(inner.name)
        ty  = self._type_name(storage.ty)
        sfx = self._suffix(ty)

        cur_val = self.new_temp()
        self.emit(f"LOAD{sfx}", inner.name, cur_val)

        one = self.new_temp()
        self.emit(f"MOV{sfx}", 1, one)
        new_val = self.new_temp()

        if node.op == '++':
            self.emit(f"ADD{sfx}", cur_val, one, new_val)
        else:
            self.emit(f"SUB{sfx}", cur_val, one, new_val)

        self.emit(f"STORE{sfx}", new_val, inner.name)
        return new_val   # valor ya modificado

    # ------------------------------------------------------------------
    # Literales
    # ------------------------------------------------------------------

    def visit(self, node: IntegerLiteral):
        tmp = self.new_temp()
        self.emit("MOVI", int(node.value), tmp)
        node.type = SimpleType('integer')
        return tmp

    def visit(self, node: FloatLiteral):
        tmp = self.new_temp()
        self.emit("MOVF", float(node.value), tmp)
        node.type = SimpleType('float')
        return tmp

    def visit(self, node: BooleanLiteral):
        tmp = self.new_temp()
        self.emit("MOVI", 1 if node.value else 0, tmp)
        node.type = SimpleType('boolean')
        return tmp

    def visit(self, node: CharLiteral):
        tmp = self.new_temp()
        val = node.value
        code = ord(val) if isinstance(val, str) and len(val) == 1 else int(val)
        self.emit("MOVB", code, tmp)
        node.type = SimpleType('char')
        return tmp

    def visit(self, node: StringLiteral):
        """
        Strings: se almacenan como DATAS (array de bytes null-terminated).
        Se devuelve un registro con la dirección (ADDR) del bloque global.
        """
        data_label = self._intern_string(node.value)
        tmp = self.new_temp()
        self.emit("ADDR", data_label, tmp)
        node.type = SimpleType('string')
        return tmp

    # ------------------------------------------------------------------
    # Nodos de tipo (no generan código)
    # ------------------------------------------------------------------

    def visit(self, node: SimpleType):
        return None

    def visit(self, node: ArrayType):
        return None

    def visit(self, node: FuncType):
        return None


# ===================================================
# Demo / prueba rápida
# ===================================================

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))

    from parser   import parse
    from checker1 import Checker

    if len(sys.argv) < 2:
        src = """
main: function integer(args:string) = {
    x: integer = 10;
    y: integer = 20;
    result: integer = x + y * 2;
    print(result);
    if (result > 10) {
        print(result);
    } else {
        print(x);
    }
    i: integer = 0;
    while (i < 3) {
        print(i);
        i = i + 1;
    }
    return result;
}
"""
        ast = parse(src)
        c = Checker.check(ast)
        if not c.ok():
            for err in c.errors:
                print(err, file=sys.stderr)
            raise SystemExit("Errores semánticos.")
        ir = IRCodeGen.generate(ast)
        print(ir.format())
    else:
        filename = sys.argv[1]
        src = open(filename, encoding="utf-8").read()
        ast = parse(src)
        c = Checker.check(ast)
        if not c.ok():
            for err in c.errors:
                print(err, file=sys.stderr)
            raise SystemExit("Errores semánticos.")
        ir = IRCodeGen.generate(ast)
        print(ir.format())
