"""
Intermediate Code Optimizer for Three Address Code (TAC).
Implements Constant Folding, Constant Propagation, Algebraic Simplification,
Copy Propagation, and Dead Code Elimination.
"""
from typing import List, Dict, Set, Tuple, Optional, Any
from .tac_instruction import TACInstruction, InstrType


class TACOptimizer:
    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations

    def optimize(self, instructions: List[TACInstruction]) -> Tuple[List[TACInstruction], Dict[str, Any]]:
        """
        Runs optimization passes iteratively until fixed point or max iterations reached.
        Returns optimized instruction list and optimization stats.
        """
        current = [self._clone_instr(i) for i in instructions]
        stats = {
            'initial_count': len(instructions),
            'constant_folds': 0,
            'algebraic_simplifications': 0,
            'copy_propagations': 0,
            'dead_instructions_removed': 0,
            'iterations': 0
        }

        for iteration in range(self.max_iterations):
            stats['iterations'] += 1
            changed = False

            # Pass 1: Constant Folding & Algebraic Simplification
            current, folds, algeb = self._pass_constant_folding(current)
            if folds > 0 or algeb > 0:
                stats['constant_folds'] += folds
                stats['algebraic_simplifications'] += algeb
                changed = True

            # Pass 2: Copy Propagation
            current, copies = self._pass_copy_propagation(current)
            if copies > 0:
                stats['copy_propagations'] += copies
                changed = True

            # Pass 3: Dead Code Elimination (unreachable instructions after goto & unused temps)
            current, dead = self._pass_dead_code_elimination(current)
            if dead > 0:
                stats['dead_instructions_removed'] += dead
                changed = True

            if not changed:
                break

        stats['final_count'] = len(current)
        stats['instructions_reduced'] = stats['initial_count'] - stats['final_count']
        return current, stats

    def _clone_instr(self, instr: TACInstruction) -> TACInstruction:
        return TACInstruction(
            op=instr.op,
            arg1=instr.arg1,
            arg2=instr.arg2,
            result=instr.result,
            instr_type=instr.instr_type,
            comment=instr.comment
        )

    def _is_number(self, val: Optional[str]) -> bool:
        if val is None:
            return False
        try:
            float(val)
            return True
        except ValueError:
            return False

    def _eval_const_bin(self, op: str, a1: str, a2: str) -> Optional[str]:
        try:
            v1 = float(a1) if '.' in a1 else int(a1)
            v2 = float(a2) if '.' in a2 else int(a2)

            res = None
            if op == '+': res = v1 + v2
            elif op == '-': res = v1 - v2
            elif op == '*': res = v1 * v2
            elif op == '/':
                if v2 == 0: return None
                res = v1 / v2 if isinstance(v1, float) or isinstance(v2, float) else v1 // v2
            elif op == '%':
                if v2 == 0: return None
                res = int(v1) % int(v2)
            elif op == '^': res = v1 ** v2
            elif op == '==': res = 1 if v1 == v2 else 0
            elif op == '!=': res = 1 if v1 != v2 else 0
            elif op == '<': res = 1 if v1 < v2 else 0
            elif op == '<=': res = 1 if v1 <= v2 else 0
            elif op == '>': res = 1 if v1 > v2 else 0
            elif op == '>=': res = 1 if v1 >= v2 else 0

            if res is not None:
                return str(res)
        except Exception:
            return None
        return None

    def _pass_constant_folding(self, instructions: List[TACInstruction]) -> Tuple[List[TACInstruction], int, int]:
        new_list = []
        folds = 0
        algeb = 0

        for instr in instructions:
            if instr.instr_type == InstrType.ASSIGN_BIN:
                # 1. Both operands are constants -> Constant Folding
                if self._is_number(instr.arg1) and self._is_number(instr.arg2):
                    folded = self._eval_const_bin(instr.op, instr.arg1, instr.arg2)
                    if folded is not None:
                        new_list.append(TACInstruction(
                            op="=",
                            arg1=folded,
                            result=instr.result,
                            instr_type=InstrType.COPY,
                            comment="[Optimized: Constant Fold]"
                        ))
                        folds += 1
                        continue

                # 2. Algebraic Simplifications
                # x + 0 = x, 0 + x = x
                if instr.op == '+' and instr.arg2 == '0':
                    new_list.append(TACInstruction(op="=", arg1=instr.arg1, result=instr.result, instr_type=InstrType.COPY))
                    algeb += 1
                    continue
                if instr.op == '+' and instr.arg1 == '0':
                    new_list.append(TACInstruction(op="=", arg1=instr.arg2, result=instr.result, instr_type=InstrType.COPY))
                    algeb += 1
                    continue
                # x - 0 = x
                if instr.op == '-' and instr.arg2 == '0':
                    new_list.append(TACInstruction(op="=", arg1=instr.arg1, result=instr.result, instr_type=InstrType.COPY))
                    algeb += 1
                    continue
                # x * 1 = x, 1 * x = x
                if instr.op == '*' and instr.arg2 == '1':
                    new_list.append(TACInstruction(op="=", arg1=instr.arg1, result=instr.result, instr_type=InstrType.COPY))
                    algeb += 1
                    continue
                if instr.op == '*' and instr.arg1 == '1':
                    new_list.append(TACInstruction(op="=", arg1=instr.arg2, result=instr.result, instr_type=InstrType.COPY))
                    algeb += 1
                    continue
                # x * 0 = 0, 0 * x = 0
                if instr.op == '*' and (instr.arg1 == '0' or instr.arg2 == '0'):
                    new_list.append(TACInstruction(op="=", arg1='0', result=instr.result, instr_type=InstrType.COPY))
                    algeb += 1
                    continue
                # x / 1 = x
                if instr.op == '/' and instr.arg2 == '1':
                    new_list.append(TACInstruction(op="=", arg1=instr.arg1, result=instr.result, instr_type=InstrType.COPY))
                    algeb += 1
                    continue

            new_list.append(instr)
        return new_list, folds, algeb

    def _pass_copy_propagation(self, instructions: List[TACInstruction]) -> Tuple[List[TACInstruction], int, int]:
        """
        Replaces usages of temporary variables that are direct copies of other values.
        Resets across labels to ensure sound basic block boundaries.
        """
        new_list = []
        copies_propagated = 0
        copies: Dict[str, str] = {}

        for instr in instructions:
            # Labels or Jumps flush copy mapping
            if instr.instr_type in (InstrType.LABEL, InstrType.GOTO, InstrType.IF_GOTO,
                                     InstrType.IF_TRUE, InstrType.IF_FALSE, InstrType.CALL):
                copies.clear()
                new_list.append(instr)
                continue

            # Substitute arg1 / arg2 if they appear in copies
            new_arg1 = copies.get(instr.arg1, instr.arg1)
            new_arg2 = copies.get(instr.arg2, instr.arg2)

            if new_arg1 != instr.arg1:
                copies_propagated += 1
            if new_arg2 != instr.arg2:
                copies_propagated += 1

            new_instr = TACInstruction(
                op=instr.op,
                arg1=new_arg1,
                arg2=new_arg2,
                result=instr.result,
                instr_type=instr.instr_type,
                comment=instr.comment
            )

            # Invalidate any copies that depended on result
            if new_instr.result:
                copies = {k: v for k, v in copies.items() if k != new_instr.result and v != new_instr.result}

            # If this is a copy instruction: tX = Y or x = Y
            if new_instr.instr_type == InstrType.COPY and new_instr.result:
                # If target is a temp variable, record copy
                if new_instr.result.startswith('t') and new_instr.result[1:].isdigit():
                    copies[new_instr.result] = new_instr.arg1

            new_list.append(new_instr)

        return new_list, copies_propagated

    def _pass_dead_code_elimination(self, instructions: List[TACInstruction]) -> Tuple[List[TACInstruction], int]:
        """
        1. Removes instructions following unconditional goto up to the next label.
        2. Removes unused temporary variable definitions.
        """
        dead_count = 0

        # Step 1: Remove unreachable code after unconditional goto
        reachable_list = []
        is_reachable = True

        for instr in instructions:
            if instr.instr_type == InstrType.LABEL:
                is_reachable = True

            if is_reachable:
                reachable_list.append(instr)
            else:
                dead_count += 1

            if instr.instr_type == InstrType.GOTO:
                is_reachable = False

        # Step 2: Identify used variables/temporaries
        used_vars: Set[str] = set()
        for instr in reachable_list:
            if instr.arg1:
                used_vars.add(instr.arg1)
            if instr.arg2:
                used_vars.add(instr.arg2)
            # In array write: arg1[arg2] = result -> result is used as a value!
            if instr.instr_type == InstrType.ARRAY_WRITE and instr.result:
                used_vars.add(instr.result)

        # Filter out unused temporary variable assignments
        final_list = []
        for instr in reachable_list:
            # If it defines a temporary variable (t1, t2...) and it is NEVER read
            if instr.result and (instr.result.startswith('t') and instr.result[1:].isdigit()):
                if instr.instr_type in (InstrType.ASSIGN_BIN, InstrType.ASSIGN_UNARY, InstrType.COPY):
                    if instr.result not in used_vars:
                        dead_count += 1
                        continue

            final_list.append(instr)

        return final_list, dead_count
