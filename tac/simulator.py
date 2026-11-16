"""
Three Address Code (TAC) Simulator / Virtual Machine.
Executes generated TAC step-by-step to verify semantic correctness and trace execution.
"""
from typing import List, Dict, Any, Optional, Tuple
from .tac_instruction import TACInstruction, InstrType


class TACSimulationError(Exception):
    pass


class TACSimulator:
    def __init__(self, instructions: List[TACInstruction], max_steps: int = 10000):
        self.instructions = instructions
        self.max_steps = max_steps
        self.variables: Dict[str, Any] = {}
        self.arrays: Dict[str, Dict[int, Any]] = {}
        self.output_log: List[str] = []
        self.label_map: Dict[str, int] = {}
        self.param_stack: List[Any] = []
        self._build_label_map()

    def _build_label_map(self):
        self.label_map.clear()
        for idx, instr in enumerate(self.instructions):
            if instr.instr_type == InstrType.LABEL and instr.result:
                self.label_map[instr.result] = idx

    def _resolve_val(self, val_str: Optional[str]) -> Any:
        if val_str is None:
            return 0
        # Check if integer literal
        try:
            return int(val_str)
        except ValueError:
            pass
        # Check if float literal
        try:
            return float(val_str)
        except ValueError:
            pass
        # Lookup in variable store
        return self.variables.get(val_str, 0)

    def run(self) -> Tuple[Dict[str, Any], List[str], List[Dict[str, Any]]]:
        """
        Executes the TAC instructions until completion or max_steps.
        Returns:
            (final_variables, output_logs, execution_trace)
        """
        ip = 0
        steps = 0
        trace: List[Dict[str, Any]] = []

        while 0 <= ip < len(self.instructions):
            if steps >= self.max_steps:
                self.output_log.append(f"[WARNING] Simulation terminated: exceeded maximum {self.max_steps} steps.")
                break

            instr = self.instructions[ip]
            steps += 1
            old_ip = ip
            next_ip = ip + 1
            changed_var = None
            changed_val = None

            itype = instr.instr_type

            if itype == InstrType.LABEL:
                pass

            elif itype == InstrType.ASSIGN_BIN:
                v1 = self._resolve_val(instr.arg1)
                v2 = self._resolve_val(instr.arg2)
                op = instr.op
                res = 0

                if op == '+': res = v1 + v2
                elif op == '-': res = v1 - v2
                elif op == '*': res = v1 * v2
                elif op == '/': res = v1 / v2 if (isinstance(v1, float) or isinstance(v2, float)) else (v1 // v2 if v2 != 0 else 0)
                elif op == '%': res = v1 % v2 if v2 != 0 else 0
                elif op == '^': res = v1 ** v2
                elif op == '==': res = 1 if v1 == v2 else 0
                elif op == '!=': res = 1 if v1 != v2 else 0
                elif op == '<': res = 1 if v1 < v2 else 0
                elif op == '<=': res = 1 if v1 <= v2 else 0
                elif op == '>': res = 1 if v1 > v2 else 0
                elif op == '>=': res = 1 if v1 >= v2 else 0
                elif op == '&&': res = 1 if (v1 != 0 and v2 != 0) else 0
                elif op == '||': res = 1 if (v1 != 0 or v2 != 0) else 0

                if instr.result:
                    self.variables[instr.result] = res
                    changed_var = instr.result
                    changed_val = res

            elif itype == InstrType.ASSIGN_UNARY:
                v1 = self._resolve_val(instr.arg1)
                res = 0
                if instr.op in ('-', 'uminus'): res = -v1
                elif instr.op == '!': res = 0 if v1 != 0 else 1
                elif instr.op == '~': res = ~int(v1)

                if instr.result:
                    self.variables[instr.result] = res
                    changed_var = instr.result
                    changed_val = res

            elif itype == InstrType.COPY:
                v1 = self._resolve_val(instr.arg1)
                if instr.result:
                    self.variables[instr.result] = v1
                    changed_var = instr.result
                    changed_val = v1

            elif itype == InstrType.GOTO:
                target = instr.result
                if target in self.label_map:
                    next_ip = self.label_map[target]
                else:
                    raise TACSimulationError(f"Undefined jump label: {target}")

            elif itype == InstrType.IF_GOTO:
                v1 = self._resolve_val(instr.arg1)
                v2 = self._resolve_val(instr.arg2)
                op = instr.op
                cond_met = False
                if op == '==': cond_met = (v1 == v2)
                elif op == '!=': cond_met = (v1 != v2)
                elif op == '<': cond_met = (v1 < v2)
                elif op == '<=': cond_met = (v1 <= v2)
                elif op == '>': cond_met = (v1 > v2)
                elif op == '>=': cond_met = (v1 >= v2)

                if cond_met:
                    target = instr.result
                    if target in self.label_map:
                        next_ip = self.label_map[target]
                    else:
                        raise TACSimulationError(f"Undefined jump label: {target}")

            elif itype == InstrType.IF_TRUE:
                v1 = self._resolve_val(instr.arg1)
                if v1 != 0:
                    target = instr.result
                    if target in self.label_map:
                        next_ip = self.label_map[target]
                    else:
                        raise TACSimulationError(f"Undefined jump label: {target}")

            elif itype == InstrType.IF_FALSE:
                v1 = self._resolve_val(instr.arg1)
                if v1 == 0:
                    target = instr.result
                    if target in self.label_map:
                        next_ip = self.label_map[target]
                    else:
                        raise TACSimulationError(f"Undefined jump label: {target}")

            elif itype == InstrType.ARRAY_READ:
                arr_name = instr.arg1 or ""
                offset = int(self._resolve_val(instr.arg2))
                val = self.arrays.get(arr_name, {}).get(offset, 0)
                if instr.result:
                    self.variables[instr.result] = val
                    changed_var = instr.result
                    changed_val = val

            elif itype == InstrType.ARRAY_WRITE:
                arr_name = instr.arg1 or ""
                offset = int(self._resolve_val(instr.arg2))
                val = self._resolve_val(instr.result)
                if arr_name not in self.arrays:
                    self.arrays[arr_name] = {}
                self.arrays[arr_name][offset] = val
                changed_var = f"{arr_name}[{offset}]"
                changed_val = val

            elif itype == InstrType.PARAM:
                v1 = self._resolve_val(instr.arg1)
                self.param_stack.append(v1)

            elif itype == InstrType.CALL:
                func_name = instr.arg1
                n_args = int(instr.arg2 or "0")
                args = [self.param_stack.pop() for _ in range(min(n_args, len(self.param_stack)))]
                args.reverse()

                # Built-in mock functions
                call_res = 0
                if func_name in ('print', 'printf'):
                    out_str = " ".join(str(a) for a in args)
                    self.output_log.append(f"[OUT] {out_str}")
                elif func_name == 'abs':
                    call_res = abs(args[0]) if args else 0
                elif func_name == 'min':
                    call_res = min(args) if args else 0
                elif func_name == 'max':
                    call_res = max(args) if args else 0

                if instr.result:
                    self.variables[instr.result] = call_res
                    changed_var = instr.result
                    changed_val = call_res

            elif itype == InstrType.RETURN:
                if instr.arg1:
                    ret_val = self._resolve_val(instr.arg1)
                    self.output_log.append(f"[RETURN] {ret_val}")
                break

            # Capture trace
            trace.append({
                'step': steps,
                'ip': old_ip,
                'instruction': instr.to_linear(),
                'changed_var': changed_var,
                'changed_val': changed_val,
                'user_vars': {k: v for k, v in self.variables.items() if not (k.startswith('t') and k[1:].isdigit())}
            })

            ip = next_ip

        # Format user variables
        user_vars = {k: v for k, v in self.variables.items() if not (k.startswith('t') and k[1:].isdigit())}
        return user_vars, self.output_log, trace
