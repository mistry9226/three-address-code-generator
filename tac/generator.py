"""
Intermediate Code Generator: Translates AST into Three Address Code (TAC).
Implements Syntax-Directed Translation (SDT) schemes.
"""
from typing import List, Optional, Tuple
from .ast_nodes import (
    ASTNode, ProgramNode, BlockNode, VarDeclNode, VarDeclarator,
    AssignNode, BinaryOpNode, UnaryOpNode, LiteralNode, VarNode,
    ArrayRefNode, IfNode, WhileNode, DoWhileNode, ForNode,
    SwitchNode, CaseNode, BreakNode, ContinueNode, ReturnNode,
    FunctionCallNode, FunctionDeclNode
)
from .tac_instruction import TACInstruction, InstrType
from .symbol_table import SymbolTable


class CodeGenerator:
    def __init__(self):
        self.instructions: List[TACInstruction] = []
        self.temp_count = 0
        self.label_count = 0
        self.symbol_table = SymbolTable()
        self.break_stack: List[str] = []
        self.continue_stack: List[str] = []

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self) -> str:
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, instr: TACInstruction) -> TACInstruction:
        self.instructions.append(instr)
        return instr

    def emit_label(self, label: str) -> TACInstruction:
        return self.emit(TACInstruction(op="label", result=label, instr_type=InstrType.LABEL))

    def emit_goto(self, label: str) -> TACInstruction:
        return self.emit(TACInstruction(op="goto", result=label, instr_type=InstrType.GOTO))

    def generate(self, root: ASTNode) -> List[TACInstruction]:
        self.instructions.clear()
        self.temp_count = 0
        self.label_count = 0
        self.break_stack.clear()
        self.continue_stack.clear()
        self.symbol_table = SymbolTable()

        self._visit(root)
        return self.instructions

    def _visit(self, node: Optional[ASTNode]) -> Optional[str]:
        if node is None:
            return None
        method = getattr(self, f"_visit_{node.__class__.__name__}", self._generic_visit)
        return method(node)

    def _generic_visit(self, node: ASTNode):
        raise NotImplementedError(f"No code generation rule for {node.__class__.__name__}")

    def _visit_ProgramNode(self, node: ProgramNode):
        for stmt in node.statements:
            self._visit(stmt)

    def _visit_BlockNode(self, node: BlockNode):
        self.symbol_table = self.symbol_table.enter_scope()
        for stmt in node.statements:
            self._visit(stmt)
        self.symbol_table = self.symbol_table.exit_scope()

    def _visit_VarDeclNode(self, node: VarDeclNode):
        for decl in node.declarators:
            dims = []
            for d in decl.array_dimensions:
                if isinstance(d, LiteralNode) and d.literal_type == 'int':
                    dims.append(int(d.value))
                else:
                    dims.append(10)  # default dimension size fallback

            self.symbol_table.define(
                name=decl.name,
                type_name=node.type_name,
                dimensions=dims,
                element_size=4
            )

            if decl.init_value:
                val = self._visit(decl.init_value)
                self.emit(TACInstruction(
                    op="=",
                    arg1=val,
                    result=decl.name,
                    instr_type=InstrType.COPY
                ))

    def _visit_AssignNode(self, node: AssignNode) -> Optional[str]:
        # Target can be VarNode or ArrayRefNode
        val = self._visit(node.value)

        # Handle compound assignment: +=, -=, *=, /=, %=
        if node.op != '=':
            base_op = node.op[:-1]  # '+=' -> '+'
            current_val = self._visit(node.target)
            t_temp = self.new_temp()
            self.emit(TACInstruction(
                op=base_op,
                arg1=current_val,
                arg2=val,
                result=t_temp,
                instr_type=InstrType.ASSIGN_BIN
            ))
            val = t_temp

        if isinstance(node.target, VarNode):
            self.emit(TACInstruction(
                op="=",
                arg1=val,
                result=node.target.name,
                instr_type=InstrType.COPY
            ))
            return node.target.name

        elif isinstance(node.target, ArrayRefNode):
            offset = self._compute_array_offset(node.target)
            self.emit(TACInstruction(
                op="[]=",
                arg1=node.target.array_name,
                arg2=offset,
                result=val,
                instr_type=InstrType.ARRAY_WRITE
            ))
            return val
        else:
            raise ValueError(f"Invalid lvalue target in assignment: {type(node.target)}")

    def _compute_array_offset(self, node: ArrayRefNode) -> str:
        """
        Computes row-major offset for multi-dimensional arrays:
        1D: A[i] -> offset = i * elem_size
        2D: A[i][j] with bounds [N, M] -> offset = (i * M + j) * elem_size
        """
        sym = self.symbol_table.lookup(node.array_name)
        elem_size = sym.element_size if sym else 4
        dims = sym.dimensions if sym and sym.dimensions else []

        if len(node.indices) == 1:
            idx = self._visit(node.indices[0])
            t_offset = self.new_temp()
            self.emit(TACInstruction(
                op="*",
                arg1=idx,
                arg2=str(elem_size),
                result=t_offset,
                instr_type=InstrType.ASSIGN_BIN
            ))
            return t_offset

        elif len(node.indices) == 2:
            i_idx = self._visit(node.indices[0])
            j_idx = self._visit(node.indices[1])
            m_bound = str(dims[1]) if len(dims) > 1 else "10"

            t1 = self.new_temp()
            self.emit(TACInstruction(
                op="*",
                arg1=i_idx,
                arg2=m_bound,
                result=t1,
                instr_type=InstrType.ASSIGN_BIN
            ))

            t2 = self.new_temp()
            self.emit(TACInstruction(
                op="+",
                arg1=t1,
                arg2=j_idx,
                result=t2,
                instr_type=InstrType.ASSIGN_BIN
            ))

            t_offset = self.new_temp()
            self.emit(TACInstruction(
                op="*",
                arg1=t2,
                arg2=str(elem_size),
                result=t_offset,
                instr_type=InstrType.ASSIGN_BIN
            ))
            return t_offset

        else:
            # General n-dimensional row-major calculation
            cur_acc = self._visit(node.indices[0])
            for d in range(1, len(node.indices)):
                dim_bound = str(dims[d]) if d < len(dims) else "10"
                t_mul = self.new_temp()
                self.emit(TACInstruction(op="*", arg1=cur_acc, arg2=dim_bound, result=t_mul, instr_type=InstrType.ASSIGN_BIN))
                next_idx = self._visit(node.indices[d])
                t_add = self.new_temp()
                self.emit(TACInstruction(op="+", arg1=t_mul, arg2=next_idx, result=t_add, instr_type=InstrType.ASSIGN_BIN))
                cur_acc = t_add

            t_final = self.new_temp()
            self.emit(TACInstruction(op="*", arg1=cur_acc, arg2=str(elem_size), result=t_final, instr_type=InstrType.ASSIGN_BIN))
            return t_final

    def _visit_ArrayRefNode(self, node: ArrayRefNode) -> str:
        offset = self._compute_array_offset(node)
        t_res = self.new_temp()
        self.emit(TACInstruction(
            op="=[]",
            arg1=node.array_name,
            arg2=offset,
            result=t_res,
            instr_type=InstrType.ARRAY_READ
        ))
        return t_res

    def _visit_BinaryOpNode(self, node: BinaryOpNode) -> str:
        # Check if it's a relational or logical operation
        if node.op in ('==', '!=', '<', '<=', '>', '>=', '&&', '||'):
            # Generate boolean evaluation into a temporary (1 or 0)
            t_res = self.new_temp()
            l_true = self.new_label()
            l_end = self.new_label()

            self._emit_condition_jump(node, true_label=l_true, false_label=None)
            self.emit(TACInstruction(op="=", arg1="0", result=t_res, instr_type=InstrType.COPY))
            self.emit_goto(l_end)
            self.emit_label(l_true)
            self.emit(TACInstruction(op="=", arg1="1", result=t_res, instr_type=InstrType.COPY))
            self.emit_label(l_end)
            return t_res

        # Standard arithmetic operation
        left_val = self._visit(node.left)
        right_val = self._visit(node.right)
        t_res = self.new_temp()
        self.emit(TACInstruction(
            op=node.op,
            arg1=left_val,
            arg2=right_val,
            result=t_res,
            instr_type=InstrType.ASSIGN_BIN
        ))
        return t_res

    def _visit_UnaryOpNode(self, node: UnaryOpNode) -> str:
        if node.op in ('++', '--'):
            target_name = node.operand.name if isinstance(node.operand, VarNode) else "var"
            op_char = '+' if node.op == '++' else '-'

            if node.is_prefix:
                # ++i : increment then return
                t_inc = self.new_temp()
                self.emit(TACInstruction(op=op_char, arg1=target_name, arg2="1", result=t_inc, instr_type=InstrType.ASSIGN_BIN))
                self.emit(TACInstruction(op="=", arg1=t_inc, result=target_name, instr_type=InstrType.COPY))
                return target_name
            else:
                # i++ : return old value then increment
                t_old = self.new_temp()
                self.emit(TACInstruction(op="=", arg1=target_name, result=t_old, instr_type=InstrType.COPY))
                t_inc = self.new_temp()
                self.emit(TACInstruction(op=op_char, arg1=target_name, arg2="1", result=t_inc, instr_type=InstrType.ASSIGN_BIN))
                self.emit(TACInstruction(op="=", arg1=t_inc, result=target_name, instr_type=InstrType.COPY))
                return t_old

        elif node.op == '!':
            val = self._visit(node.operand)
            t_res = self.new_temp()
            l_true = self.new_label()
            l_end = self.new_label()
            self.emit(TACInstruction(op="ifFalse", arg1=val, result=l_true, instr_type=InstrType.IF_FALSE))
            self.emit(TACInstruction(op="=", arg1="0", result=t_res, instr_type=InstrType.COPY))
            self.emit_goto(l_end)
            self.emit_label(l_true)
            self.emit(TACInstruction(op="=", arg1="1", result=t_res, instr_type=InstrType.COPY))
            self.emit_label(l_end)
            return t_res

        else:
            val = self._visit(node.operand)
            t_res = self.new_temp()
            self.emit(TACInstruction(
                op=node.op,
                arg1=val,
                result=t_res,
                instr_type=InstrType.ASSIGN_UNARY
            ))
            return t_res

    def _visit_LiteralNode(self, node: LiteralNode) -> str:
        return str(node.value)

    def _visit_VarNode(self, node: VarNode) -> str:
        return node.name

    def _emit_condition_jump(self, cond: ASTNode, true_label: Optional[str] = None, false_label: Optional[str] = None):
        """
        Emits conditional jumps for relational/logical conditions.
        """
        if isinstance(cond, BinaryOpNode):
            if cond.op in ('<', '<=', '>', '>=', '==', '!='):
                left_val = self._visit(cond.left)
                right_val = self._visit(cond.right)
                if true_label:
                    self.emit(TACInstruction(
                        op=cond.op,
                        arg1=left_val,
                        arg2=right_val,
                        result=true_label,
                        instr_type=InstrType.IF_GOTO
                    ))
                elif false_label:
                    # Invert the operator for false_label
                    inv_map = {'<': '>=', '<=': '>', '>': '<=', '>=': '<', '==': '!=', '!=': '=='}
                    self.emit(TACInstruction(
                        op=inv_map[cond.op],
                        arg1=left_val,
                        arg2=right_val,
                        result=false_label,
                        instr_type=InstrType.IF_GOTO
                    ))
                return

            elif cond.op == '&&':
                if false_label:
                    self._emit_condition_jump(cond.left, true_label=None, false_label=false_label)
                    self._emit_condition_jump(cond.right, true_label=None, false_label=false_label)
                elif true_label:
                    l_next = self.new_label()
                    l_skip = self.new_label()
                    self._emit_condition_jump(cond.left, true_label=l_next, false_label=l_skip)
                    self.emit_label(l_next)
                    self._emit_condition_jump(cond.right, true_label=true_label, false_label=None)
                    self.emit_label(l_skip)
                return

            elif cond.op == '||':
                if true_label:
                    self._emit_condition_jump(cond.left, true_label=true_label, false_label=None)
                    self._emit_condition_jump(cond.right, true_label=true_label, false_label=None)
                elif false_label:
                    l_skip = self.new_label()
                    self._emit_condition_jump(cond.left, true_label=l_skip, false_label=None)
                    self._emit_condition_jump(cond.right, true_label=None, false_label=false_label)
                    self.emit_label(l_skip)
                return

        val = self._visit(cond)
        if false_label:
            self.emit(TACInstruction(op="ifFalse", arg1=val, result=false_label, instr_type=InstrType.IF_FALSE))
        elif true_label:
            self.emit(TACInstruction(op="ifTrue", arg1=val, result=true_label, instr_type=InstrType.IF_TRUE))

    def _visit_IfNode(self, node: IfNode):
        l_else = self.new_label()
        l_end = self.new_label()

        if node.else_branch:
            self._emit_condition_jump(node.condition, true_label=None, false_label=l_else)
            self._visit(node.then_branch)
            self.emit_goto(l_end)
            self.emit_label(l_else)
            self._visit(node.else_branch)
            self.emit_label(l_end)
        else:
            self._emit_condition_jump(node.condition, true_label=None, false_label=l_end)
            self._visit(node.then_branch)
            self.emit_label(l_end)

    def _visit_WhileNode(self, node: WhileNode):
        l_start = self.new_label()
        l_end = self.new_label()

        self.break_stack.append(l_end)
        self.continue_stack.append(l_start)

        self.emit_label(l_start)
        self._emit_condition_jump(node.condition, true_label=None, false_label=l_end)
        self._visit(node.body)
        self.emit_goto(l_start)
        self.emit_label(l_end)

        self.break_stack.pop()
        self.continue_stack.pop()

    def _visit_DoWhileNode(self, node: DoWhileNode):
        l_start = self.new_label()
        l_cond = self.new_label()
        l_end = self.new_label()

        self.break_stack.append(l_end)
        self.continue_stack.append(l_cond)

        self.emit_label(l_start)
        self._visit(node.body)
        self.emit_label(l_cond)
        self._emit_condition_jump(node.condition, true_label=l_start, false_label=None)
        self.emit_label(l_end)

        self.break_stack.pop()
        self.continue_stack.pop()

    def _visit_ForNode(self, node: ForNode):
        l_cond = self.new_label()
        l_step = self.new_label()
        l_end = self.new_label()

        if node.init:
            self._visit(node.init)

        self.break_stack.append(l_end)
        self.continue_stack.append(l_step)

        self.emit_label(l_cond)
        if node.condition:
            self._emit_condition_jump(node.condition, true_label=None, false_label=l_end)

        self._visit(node.body)

        self.emit_label(l_step)
        if node.step:
            self._visit(node.step)

        self.emit_goto(l_cond)
        self.emit_label(l_end)

        self.break_stack.pop()
        self.continue_stack.pop()

    def _visit_SwitchNode(self, node: SwitchNode):
        sw_val = self._visit(node.expr)
        l_end = self.new_label()
        self.break_stack.append(l_end)

        case_labels = []
        default_label = None

        for case in node.cases:
            l_case = self.new_label()
            if case.value is not None:
                c_val = self._visit(case.value)
                t_eq = self.new_temp()
                self.emit(TACInstruction(op="==", arg1=sw_val, arg2=c_val, result=t_eq, instr_type=InstrType.ASSIGN_BIN))
                self.emit(TACInstruction(op="ifTrue", arg1=t_eq, result=l_case, instr_type=InstrType.IF_TRUE))
                case_labels.append((l_case, case))
            else:
                default_label = l_case
                case_labels.append((l_case, case))

        if default_label:
            self.emit_goto(default_label)
        else:
            self.emit_goto(l_end)

        for l_lbl, case in case_labels:
            self.emit_label(l_lbl)
            for stmt in case.statements:
                self._visit(stmt)

        self.emit_label(l_end)
        self.break_stack.pop()

    def _visit_BreakNode(self, node: BreakNode):
        if not self.break_stack:
            raise ValueError("'break' statement not inside loop or switch")
        self.emit_goto(self.break_stack[-1])

    def _visit_ContinueNode(self, node: ContinueNode):
        if not self.continue_stack:
            raise ValueError("'continue' statement not inside loop")
        self.emit_goto(self.continue_stack[-1])

    def _visit_ReturnNode(self, node: ReturnNode):
        val = self._visit(node.expr) if node.expr else None
        self.emit(TACInstruction(op="return", arg1=val, instr_type=InstrType.RETURN))

    def _visit_FunctionCallNode(self, node: FunctionCallNode) -> str:
        arg_vals = [self._visit(arg) for arg in node.arguments]
        for a in arg_vals:
            self.emit(TACInstruction(op="param", arg1=a, instr_type=InstrType.PARAM))

        t_res = self.new_temp()
        self.emit(TACInstruction(
            op="call",
            arg1=node.name,
            arg2=str(len(arg_vals)),
            result=t_res,
            instr_type=InstrType.CALL
        ))
        return t_res

    def _visit_FunctionDeclNode(self, node: FunctionDeclNode):
        self.emit_label(f"func_{node.name}")
        self._visit(node.body)
        self.emit(TACInstruction(op="return", instr_type=InstrType.RETURN))
