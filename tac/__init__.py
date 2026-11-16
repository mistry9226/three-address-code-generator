"""
Three Address Code (TAC) Generator Package.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .tokens import Token, TokenType
from .lexer import Lexer, LexerError
from .ast_nodes import ASTNode, ProgramNode
from .parser import Parser, ParserError
from .tac_instruction import TACInstruction, Triple, convert_tac_to_triples
from .generator import CodeGenerator
from .optimizer import TACOptimizer
from .cfg import ControlFlowGraph
from .simulator import TACSimulator


@dataclass
class CompilationResult:
    source: str
    tokens: List[Token]
    ast: ProgramNode
    tac_instructions: List[TACInstruction]
    linear_tac: str
    quadruples: List[Dict[str, str]]
    triples: List[Dict[str, str]]
    indirect_triples: List[Dict[str, Any]]
    cfg: ControlFlowGraph
    optimized_instructions: Optional[List[TACInstruction]] = None
    optimized_linear_tac: Optional[str] = None
    optimizer_stats: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'linear_tac': self.linear_tac,
            'quadruples': self.quadruples,
            'triples': self.triples,
            'indirect_triples': self.indirect_triples,
            'ast': self.ast.to_dict(),
            'cfg': self.cfg.to_dict(),
            'optimized_linear_tac': self.optimized_linear_tac,
            'optimizer_stats': self.optimizer_stats
        }


def compile_to_tac(source: str, optimize: bool = False) -> CompilationResult:
    """
    Full pipeline: Source -> Tokens -> AST -> TAC -> Quadruples/Triples -> CFG -> [Optimizer]
    """
    # 1. Lexical Analysis
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    # 2. Syntax Analysis
    parser = Parser(tokens)
    ast = parser.parse()

    # 3. Intermediate Code Generation
    generator = CodeGenerator()
    instructions = generator.generate(ast)

    linear_tac = "\n".join(i.to_linear() for i in instructions)

    # 4. Quadruples
    quads = []
    for idx, i in enumerate(instructions):
        op, a1, a2, res = i.to_quadruple()
        quads.append({
            'index': idx,
            'op': op,
            'arg1': a1,
            'arg2': a2,
            'result': res
        })

    # 5. Triples & Indirect Triples
    triples_list, indirect_ptr = convert_tac_to_triples(instructions)
    triples_dict = [t.to_dict() for t in triples_list]
    indirect_dict = []
    for ptr_idx, stmt_idx in enumerate(indirect_ptr):
        t_ref = triples_list[stmt_idx] if stmt_idx < len(triples_list) else None
        indirect_dict.append({
            'pointer': f"[{ptr_idx}]",
            'statement': f"({stmt_idx})",
            'op': t_ref.op if t_ref else "",
            'arg1': t_ref.arg1 if t_ref else "",
            'arg2': t_ref.arg2 if t_ref else ""
        })

    # 6. Control Flow Graph
    cfg = ControlFlowGraph(instructions)

    # 7. Optimization Pass (Optional)
    opt_instructions = None
    opt_linear_tac = None
    stats = None

    if optimize:
        optimizer = TACOptimizer()
        opt_instructions, stats = optimizer.optimize(instructions)
        opt_linear_tac = "\n".join(i.to_linear() for i in opt_instructions)

    return CompilationResult(
        source=source,
        tokens=tokens,
        ast=ast,
        tac_instructions=instructions,
        linear_tac=linear_tac,
        quadruples=quads,
        triples=triples_dict,
        indirect_triples=indirect_dict,
        cfg=cfg,
        optimized_instructions=opt_instructions,
        optimized_linear_tac=opt_linear_tac,
        optimizer_stats=stats
    )


def simulate_tac(instructions: List[TACInstruction], max_steps: int = 10000):
    simulator = TACSimulator(instructions, max_steps=max_steps)
    return simulator.run()
