"""
Three Address Code (TAC) Instruction representations:
Linear TAC, Quadruples, Triples, and Indirect Triples.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Tuple


class InstrType(Enum):
    LABEL = auto()
    ASSIGN_BIN = auto()      # res = arg1 op arg2
    ASSIGN_UNARY = auto()    # res = op arg1
    COPY = auto()            # res = arg1
    GOTO = auto()            # goto label
    IF_GOTO = auto()         # if arg1 relop arg2 goto label
    IF_TRUE = auto()         # if arg1 goto label
    IF_FALSE = auto()        # ifFalse arg1 goto label
    ARRAY_READ = auto()      # res = arg1[arg2]
    ARRAY_WRITE = auto()     # arg1[arg2] = res
    PARAM = auto()           # param arg1
    CALL = auto()            # res = call func, n
    RETURN = auto()          # return arg1


@dataclass
class TACInstruction:
    op: str
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    result: Optional[str] = None
    instr_type: InstrType = InstrType.COPY
    comment: str = ""

    def to_linear(self) -> str:
        """Render as standard human-readable Three Address Code."""
        if self.instr_type == InstrType.LABEL:
            return f"{self.result}:"

        if self.instr_type == InstrType.ASSIGN_BIN:
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"

        if self.instr_type == InstrType.ASSIGN_UNARY:
            op_disp = '-' if self.op == 'uminus' else self.op
            return f"{self.result} = {op_disp}{self.arg1}"

        if self.instr_type == InstrType.COPY:
            return f"{self.result} = {self.arg1}"

        if self.instr_type == InstrType.GOTO:
            return f"goto {self.result}"

        if self.instr_type == InstrType.IF_GOTO:
            return f"if {self.arg1} {self.op} {self.arg2} goto {self.result}"

        if self.instr_type == InstrType.IF_TRUE:
            return f"if {self.arg1} goto {self.result}"

        if self.instr_type == InstrType.IF_FALSE:
            return f"ifFalse {self.arg1} goto {self.result}"

        if self.instr_type == InstrType.ARRAY_READ:
            return f"{self.result} = {self.arg1}[{self.arg2}]"

        if self.instr_type == InstrType.ARRAY_WRITE:
            return f"{self.arg1}[{self.arg2}] = {self.result}"

        if self.instr_type == InstrType.PARAM:
            return f"param {self.arg1}"

        if self.instr_type == InstrType.CALL:
            if self.result:
                return f"{self.result} = call {self.arg1}, {self.arg2}"
            return f"call {self.arg1}, {self.arg2}"

        if self.instr_type == InstrType.RETURN:
            if self.arg1:
                return f"return {self.arg1}"
            return "return"

        return f"{self.op} {self.arg1} {self.arg2} {self.result}".strip()

    def to_quadruple(self) -> Tuple[str, str, str, str]:
        """Return (op, arg1, arg2, result) tuple."""
        op_str = self.op
        if self.instr_type == InstrType.ARRAY_READ:
            op_str = "=[]"
        elif self.instr_type == InstrType.ARRAY_WRITE:
            op_str = "[]="
        elif self.instr_type == InstrType.COPY:
            op_str = "="
        elif self.instr_type == InstrType.IF_GOTO:
            op_str = f"if {self.op}"
        elif self.instr_type == InstrType.IF_FALSE:
            op_str = "ifFalse"
        elif self.instr_type == InstrType.IF_TRUE:
            op_str = "ifTrue"

        arg1_str = str(self.arg1) if self.arg1 is not None else ""
        arg2_str = str(self.arg2) if self.arg2 is not None else ""
        res_str = str(self.result) if self.result is not None else ""

        return (op_str, arg1_str, arg2_str, res_str)

    def to_dict(self) -> Dict[str, Any]:
        quad = self.to_quadruple()
        return {
            'linear': self.to_linear(),
            'op': quad[0],
            'arg1': quad[1],
            'arg2': quad[2],
            'result': quad[3],
            'type': self.instr_type.name,
            'comment': self.comment
        }


@dataclass
class Triple:
    index: int
    op: str
    arg1: str
    arg2: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'index': f"({self.index})",
            'op': self.op,
            'arg1': self.arg1,
            'arg2': self.arg2
        }


def convert_tac_to_triples(instructions: List[TACInstruction]) -> Tuple[List[Triple], List[int]]:
    """
    Converts a sequence of TAC instructions into Triples and Indirect Triples pointer list.
    Maps temporary variables (t1, t2, ...) to their producing triple index: (0), (1), etc.
    """
    triples: List[Triple] = []
    indirect_pointers: List[int] = []
    temp_to_triple: Dict[str, str] = {}

    def resolve_arg(arg: Optional[str]) -> str:
        if arg is None:
            return ""
        if arg in temp_to_triple:
            return temp_to_triple[arg]
        return str(arg)

    for i, instr in enumerate(instructions):
        t_idx = len(triples)
        indirect_pointers.append(t_idx)

        op_str, a1, a2, res = instr.to_quadruple()
        resolved_a1 = resolve_arg(a1)
        resolved_a2 = resolve_arg(a2)

        if instr.instr_type == InstrType.ASSIGN_BIN:
            triple = Triple(index=t_idx, op=instr.op, arg1=resolved_a1, arg2=resolved_a2)
            triples.append(triple)
            if instr.result and (instr.result.startswith('t') and instr.result[1:].isdigit()):
                temp_to_triple[instr.result] = f"({t_idx})"

        elif instr.instr_type == InstrType.ASSIGN_UNARY:
            op_disp = '-' if instr.op == 'uminus' else instr.op
            triple = Triple(index=t_idx, op=op_disp, arg1=resolved_a1, arg2="")
            triples.append(triple)
            if instr.result and (instr.result.startswith('t') and instr.result[1:].isdigit()):
                temp_to_triple[instr.result] = f"({t_idx})"

        elif instr.instr_type == InstrType.COPY:
            # In triples, assignment to user variable is: = target source
            # e.g., op='=', arg1='x', arg2='(0)'
            triple = Triple(index=t_idx, op="=", arg1=res, arg2=resolved_a1)
            triples.append(triple)
            if instr.result and (instr.result.startswith('t') and instr.result[1:].isdigit()):
                temp_to_triple[instr.result] = f"({t_idx})"

        elif instr.instr_type == InstrType.ARRAY_READ:
            triple = Triple(index=t_idx, op="=[]", arg1=resolved_a1, arg2=resolved_a2)
            triples.append(triple)
            if instr.result and (instr.result.startswith('t') and instr.result[1:].isdigit()):
                temp_to_triple[instr.result] = f"({t_idx})"

        elif instr.instr_type == InstrType.ARRAY_WRITE:
            resolved_res = resolve_arg(res)
            # []= arr index val
            triple = Triple(index=t_idx, op="[]=", arg1=f"{resolved_a1}[{resolved_a2}]", arg2=resolved_res)
            triples.append(triple)

        elif instr.instr_type == InstrType.GOTO:
            triple = Triple(index=t_idx, op="goto", arg1=res, arg2="")
            triples.append(triple)

        elif instr.instr_type in (InstrType.IF_GOTO, InstrType.IF_FALSE, InstrType.IF_TRUE):
            triple = Triple(index=t_idx, op=op_str, arg1=resolved_a1 if resolved_a1 else resolved_res, arg2=res)
            triples.append(triple)

        elif instr.instr_type == InstrType.LABEL:
            triple = Triple(index=t_idx, op="label", arg1=res, arg2="")
            triples.append(triple)

        elif instr.instr_type == InstrType.PARAM:
            triple = Triple(index=t_idx, op="param", arg1=resolved_a1, arg2="")
            triples.append(triple)

        elif instr.instr_type == InstrType.CALL:
            triple = Triple(index=t_idx, op="call", arg1=resolved_a1, arg2=resolved_a2)
            triples.append(triple)
            if instr.result and (instr.result.startswith('t') and instr.result[1:].isdigit()):
                temp_to_triple[instr.result] = f"({t_idx})"

        elif instr.instr_type == InstrType.RETURN:
            triple = Triple(index=t_idx, op="return", arg1=resolved_a1, arg2="")
            triples.append(triple)

        else:
            triple = Triple(index=t_idx, op=op_str, arg1=resolved_a1, arg2=resolved_a2)
            triples.append(triple)

    return triples, indirect_pointers
