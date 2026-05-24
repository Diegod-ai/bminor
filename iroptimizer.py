from __future__ import annotations

import sys
from typing import Any, Optional

from ircode import IRProgram, IRFunction, Instruction, IRCodeGen

class IROptimizer:
    def __init__(self, level: int = 0):
        self.level = level

    @classmethod
    def optimize(cls, program: IRProgram, level: int = 0) -> IRProgram:
        return cls(level).visit_program(program)

    def visit_program(self, program: IRProgram) -> IRProgram:
        if self.level <= 0:
            return program

        new_globals = list(program.globals)
        new_functions: list[IRFunction] = []

        for fn in program.functions:
            new_insts = self.optimize_instruction_list(fn.instructions)
            new_functions.append(
                IRFunction(
                    name=fn.name,
                    params=list(fn.params),
                    return_type=fn.return_type,
                    instructions=new_insts,
                )
            )

        return IRProgram(globals=new_globals, functions=new_functions)

    def optimize_instruction_list(self, instructions: list[Instruction]) -> list[Instruction]:
        insts = list(instructions)

        if self.level >= 1:
            insts = self.constant_fold_and_simplify(insts)
            insts = self.remove_unreachable(insts)
            insts = self.remove_branch_to_next_label(insts)

        if self.level >= 2:
            insts = self.remove_unused_temp_definitions(insts)

        return insts

    # -------------------------------------------------
    # Nivel O1
    # -------------------------------------------------

    def constant_fold_and_simplify(self, instructions: list[Instruction]) -> list[Instruction]:
        const: dict[str, Any] = {}
        out: list[Instruction] = []

        for inst in instructions:
            op = inst[0]

            if op in {"MOVI", "MOVF", "MOVB"} and len(inst) == 3:
                value, dst = inst[1], inst[2]
                const[dst] = value
                out.append(inst)
                continue

            if op in {"ADDI", "SUBI", "MULI", "DIVI", "ADDF", "SUBF", "MULF", "DIVF"} and len(inst) == 4:
                a, b, dst = inst[1], inst[2], inst[3]

                val_a = const.get(a, a)
                val_b = const.get(b, b)

                
                # Si a y b son constantes, evaluar la operación.
                # Reemplazar por MOVI o MOVF.
                # No optimizar división por cero.
                if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                    # Verificar división por cero
                    if (op == "DIVI" and val_b == 0) or (op == "DIVF" and val_b == 0.0):
                        pass # Conservamos la instrucción original
                    else:
                        res = 0
                        if op.startswith("ADD"): res = val_a + val_b
                        elif op.startswith("SUB"): res = val_a - val_b
                        elif op.startswith("MUL"): res = val_a * val_b
                        elif op.startswith("DIV"): 
                            res = val_a // val_b if op.endswith("I") else val_a / val_b
                        
                        mov_op = "MOVF" if op.endswith("F") else "MOVI"
                        out.append((mov_op, res, dst))
                        const[dst] = res
                        continue

               
                # Aplicar reglas algebraicas simples.
                if op == "ADDI" or op == "ADDF":
                    if val_b == 0:
                        out.append(("MOVI" if op.endswith("I") else "MOVF", val_a, dst))
                        const[dst] = val_a
                        continue
                    elif val_a == 0:
                        out.append(("MOVI" if op.endswith("I") else "MOVF", val_b, dst))
                        const[dst] = val_b
                        continue
                elif op == "SUBI" or op == "SUBF":
                    if val_b == 0:
                        out.append(("MOVI" if op.endswith("I") else "MOVF", val_a, dst))
                        const[dst] = val_a
                        continue
                elif op == "MULI" or op == "MULF":
                    if val_b == 1:
                        out.append(("MOVI" if op.endswith("I") else "MOVF", val_a, dst))
                        const[dst] = val_a
                        continue
                    elif val_a == 1:
                        out.append(("MOVI" if op.endswith("I") else "MOVF", val_b, dst))
                        const[dst] = val_b
                        continue
                    elif val_b == 0 or val_a == 0:
                        out.append(("MOVI" if op.endswith("I") else "MOVF", 0, dst))
                        const[dst] = 0
                        continue
                elif op == "DIVI" or op == "DIVF":
                    if val_b == 1:
                        out.append(("MOVI" if op.endswith("I") else "MOVF", val_a, dst))
                        const[dst] = val_a
                        continue

                const.pop(dst, None)
                out.append(inst)
                continue

            if op in {"CMPI", "CMPF", "CMPB"} and len(inst) == 5:
                cmp_oper, a, b, dst = inst[1], inst[2], inst[3], inst[4]

                val_a = const.get(a, a)
                val_b = const.get(b, b)

                
                # Si a y b son constantes, reemplazar por MOVI 1 o MOVI 0.
                if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                    res = 1 if self.eval_cmp(cmp_oper, val_a, val_b) else 0
                    out.append(("MOVI", res, dst))
                    const[dst] = res
                    continue

                const.pop(dst, None)
                out.append(inst)
                continue

            if op == "CBRANCH" and len(inst) == 4:
                test, true_label, false_label = inst[1], inst[2], inst[3]

                val_test = const.get(test, test)

                
                # Si test es constante, reemplazar por BRANCH true_label o false_label.
                if isinstance(val_test, (int, float)):
                    target_label = true_label if val_test != 0 else false_label
                    out.append(("BRANCH", target_label))
                    continue

                out.append(inst)
                continue

            # Instrucciones conservadoras.
            if len(inst) >= 2 and isinstance(inst[-1], str) and inst[-1].startswith("R"):
                const.pop(inst[-1], None)

            out.append(inst)

        return out

    def remove_unreachable(self, instructions: list[Instruction]) -> list[Instruction]:
        out: list[Instruction] = []
        unreachable = False

        for inst in instructions:
            op = inst[0]

           
            # Si llega un LABEL, termina la zona inalcanzable.
            if op == "LABEL":
                unreachable = False
                out.append(inst)
                continue

            # Si estamos en zona inalcanzable, descartar la instrucción.
            if unreachable:
                continue

            out.append(inst)
            
            # Si se ve BRANCH o RET, marcar unreachable = True.
            if op in {"BRANCH", "RET"}:
                unreachable = True

        return out

    def remove_branch_to_next_label(self, instructions: list[Instruction]) -> list[Instruction]:
        out: list[Instruction] = []
        i = 0

        while i < len(instructions):
            inst = instructions[i]

        
            # Si inst es BRANCH Lx y la siguiente instrucción es LABEL Lx,
            # eliminar el BRANCH.
            if inst[0] == "BRANCH" and (i + 1 < len(instructions)):
                next_inst = instructions[i + 1]
                if next_inst[0] == "LABEL" and inst[1] == next_inst[1]:
                    i += 1
                    continue

            out.append(inst)
            i += 1

        return out

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------

    def eval_cmp(self, oper: str, a: Any, b: Any) -> bool:
        if oper == "==":
            return a == b
        if oper == "!=":
            return a != b
        if oper == "<":
            return a < b
        if oper == "<=":
            return a <= b
        if oper == ">":
            return a > b
        if oper == ">=":
            return a >= b
        raise NotImplementedError(f"Comparador no soportado: {oper}")


# ==================================================
# Interfaz de Línea de Comandos (CLI)
# ==================================================

def parse_opt_level(value: str) -> int:
    text = str(value).strip()

    if text.startswith("-O"):
        text = text[2:]
    elif text.startswith("O"):
        text = text[1:]

    if not text.isdigit():
        raise ValueError(f"Nivel de optimización inválido: {value!r}")

    level = int(text)

    if level < 0 or level > 4:
        raise ValueError("El nivel de optimización debe estar entre 0 y 4")

    return level

if __name__ == "__main__":
    from parser import parse
    from checker1 import Checker

    if len(sys.argv) < 2:
        print("Uso: python iroptimizer.py archivo.bminor [-O0 | -O1 | -O2]")
        sys.exit(1)

    filename = sys.argv[1]
    
    # Por defecto, asumimos O0 si no se proporciona nivel
    level_arg = "-O0"
    if len(sys.argv) >= 3:
        level_arg = sys.argv[2]
        # Soporte para formato `python iroptimizer.py archivo.bminor -O 2`
        if level_arg == "-O" and len(sys.argv) >= 4:
            level_arg = f"-O{sys.argv[3]}"

    try:
        opt_level = parse_opt_level(level_arg)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        with open(filename, encoding="utf-8") as f:
            src = f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{filename}'.")
        sys.exit(1)

    # 1. Parseo
    ast = parse(src)

    # 2. Análisis semántico
    c = Checker.check(ast)
    if not c.ok():
        for err in c.errors:
            print(err, file=sys.stderr)
        raise SystemExit("Errores semánticos. No se puede generar IR.")

    # 3. Generación de IR
    ir_program = IRCodeGen.generate(ast)

    if opt_level == 0:
        print(f"--- IR ORIGINAL (-O0) ---")
        print(ir_program.format())
    else:
        # 4. Optimización
        opt_program = IROptimizer.optimize(ir_program, level=opt_level)
        print(f"--- IR OPTIMIZADO (-O{opt_level}) ---")
        print(opt_program.format())