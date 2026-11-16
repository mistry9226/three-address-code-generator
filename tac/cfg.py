"""
Basic Block Partitioning and Control Flow Graph (CFG) Generator.
Implements the canonical Dragon Book Leader Identification algorithm.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from .tac_instruction import TACInstruction, InstrType


@dataclass
class BasicBlock:
    id: int
    name: str
    instructions: List[TACInstruction] = field(default_factory=list)
    predecessors: List['BasicBlock'] = field(default_factory=list)
    successors: List['BasicBlock'] = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False

    def to_linear(self) -> str:
        lines = [f"--- {self.name} ---"]
        for instr in self.instructions:
            lines.append(f"  {instr.to_linear()}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'instructions': [i.to_linear() for i in self.instructions],
            'predecessors': [p.name for p in self.predecessors],
            'successors': [s.name for s in self.successors]
        }


class ControlFlowGraph:
    def __init__(self, instructions: List[TACInstruction]):
        self.instructions = instructions
        self.blocks: List[BasicBlock] = []
        self._build_cfg()

    def _build_cfg(self):
        if not self.instructions:
            return

        n = len(self.instructions)
        # Step 1: Identify Leaders
        leaders: Set[int] = {0}
        label_to_index: Dict[str, int] = {}

        # Map labels to their instruction index
        for idx, instr in enumerate(self.instructions):
            if instr.instr_type == InstrType.LABEL and instr.result:
                label_to_index[instr.result] = idx

        for idx, instr in enumerate(self.instructions):
            # Target of jump is a leader
            if instr.instr_type in (InstrType.GOTO, InstrType.IF_GOTO, InstrType.IF_TRUE, InstrType.IF_FALSE):
                target_label = instr.result
                if target_label in label_to_index:
                    leaders.add(label_to_index[target_label])
                # Instruction immediately following jump is a leader
                if idx + 1 < n:
                    leaders.add(idx + 1)

            elif instr.instr_type == InstrType.RETURN:
                if idx + 1 < n:
                    leaders.add(idx + 1)

            elif instr.instr_type == InstrType.LABEL:
                leaders.add(idx)

        sorted_leaders = sorted(list(leaders))

        # Step 2: Form Basic Blocks from leaders
        self.blocks = []
        block_map: Dict[int, BasicBlock] = {}
        label_to_block: Dict[str, BasicBlock] = {}

        for b_idx, start_idx in enumerate(sorted_leaders):
            end_idx = sorted_leaders[b_idx + 1] if b_idx + 1 < len(sorted_leaders) else n
            block_instrs = self.instructions[start_idx:end_idx]
            block = BasicBlock(
                id=b_idx + 1,
                name=f"B{b_idx + 1}",
                instructions=block_instrs,
                is_entry=(b_idx == 0)
            )
            self.blocks.append(block)
            block_map[start_idx] = block

            # Register any labels in this block
            for instr in block_instrs:
                if instr.instr_type == InstrType.LABEL and instr.result:
                    label_to_block[instr.result] = block

        # Step 3: Add Control Flow Edges
        for b_idx, block in enumerate(self.blocks):
            if not block.instructions:
                continue

            last_instr = block.instructions[-1]

            if last_instr.instr_type == InstrType.GOTO:
                target_lbl = last_instr.result
                if target_lbl and target_lbl in label_to_block:
                    target_b = label_to_block[target_lbl]
                    self._add_edge(block, target_b)

            elif last_instr.instr_type in (InstrType.IF_GOTO, InstrType.IF_TRUE, InstrType.IF_FALSE):
                # Branch edge to target
                target_lbl = last_instr.result
                if target_lbl and target_lbl in label_to_block:
                    target_b = label_to_block[target_lbl]
                    self._add_edge(block, target_b)

                # Fallthrough edge to next block
                if b_idx + 1 < len(self.blocks):
                    self._add_edge(block, self.blocks[b_idx + 1])

            elif last_instr.instr_type == InstrType.RETURN:
                block.is_exit = True

            else:
                # Normal fallthrough to next block
                if b_idx + 1 < len(self.blocks):
                    self._add_edge(block, self.blocks[b_idx + 1])

    def _add_edge(self, from_b: BasicBlock, to_b: BasicBlock):
        if to_b not in from_b.successors:
            from_b.successors.append(to_b)
        if from_b not in to_b.predecessors:
            to_b.predecessors.append(from_b)

    def to_mermaid(self) -> str:
        """Generates Mermaid flowchart representation of the CFG."""
        lines = ["flowchart TD"]

        for b in self.blocks:
            # Escape HTML and quotes
            instr_lines = []
            for instr in b.instructions:
                clean_text = instr.to_linear().replace('"', "'")
                instr_lines.append(clean_text)
            content = "<br/>".join(instr_lines) if instr_lines else "empty"
            node_label = f"<b>{b.name}</b><br/>{content}"
            lines.append(f'    {b.name}["{node_label}"]')

        for b in self.blocks:
            for s in b.successors:
                # Determine edge label if last instruction is conditional
                edge_label = ""
                if b.instructions and b.instructions[-1].instr_type in (InstrType.IF_GOTO, InstrType.IF_TRUE, InstrType.IF_FALSE):
                    last = b.instructions[-1]
                    target_lbl = last.result
                    # Check if s contains this label
                    contains_target = any(i.result == target_lbl for i in s.instructions if i.instr_type == InstrType.LABEL)
                    if contains_target:
                        edge_label = " -- True --> "
                    else:
                        edge_label = " -- False / Next --> "
                else:
                    edge_label = " --> "

                lines.append(f"    {b.name}{edge_label}{s.name}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'blocks': [b.to_dict() for b in self.blocks],
            'mermaid': self.to_mermaid()
        }
