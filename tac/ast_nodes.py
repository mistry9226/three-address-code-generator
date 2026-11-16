"""
Abstract Syntax Tree (AST) node definitions.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


@dataclass
class ASTNode:
    line: int = 0
    column: int = 0

    def accept(self, visitor: Any) -> Any:
        method_name = f'visit_{self.__class__.__name__}'
        visitor_fn = getattr(visitor, method_name, visitor.generic_visit)
        return visitor_fn(self)

    def to_dict(self) -> Dict[str, Any]:
        """Convert AST to dictionary representation for JSON / UI rendering."""
        res = {'type': self.__class__.__name__}
        for k, v in self.__dict__.items():
            if k in ('line', 'column'):
                continue
            if isinstance(v, ASTNode):
                res[k] = v.to_dict()
            elif isinstance(v, list):
                res[k] = [item.to_dict() if isinstance(item, ASTNode) else item for item in v]
            else:
                res[k] = v
        return res


@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class BlockNode(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class VarDeclarator(ASTNode):
    name: str = ""
    array_dimensions: List[ASTNode] = field(default_factory=list)  # e.g., [10, 20] for a[10][20]
    init_value: Optional[ASTNode] = None


@dataclass
class VarDeclNode(ASTNode):
    type_name: str = "int"
    declarators: List[VarDeclarator] = field(default_factory=list)


@dataclass
class AssignNode(ASTNode):
    target: ASTNode = None  # VarNode or ArrayRefNode
    op: str = "="          # '=', '+=', '-=', etc.
    value: ASTNode = None


@dataclass
class BinaryOpNode(ASTNode):
    op: str = ""
    left: ASTNode = None
    right: ASTNode = None


@dataclass
class UnaryOpNode(ASTNode):
    op: str = ""
    operand: ASTNode = None
    is_prefix: bool = True  # True for ++x, False for x++


@dataclass
class LiteralNode(ASTNode):
    value: Any = None
    literal_type: str = "int"  # 'int', 'float', 'string'


@dataclass
class VarNode(ASTNode):
    name: str = ""


@dataclass
class ArrayRefNode(ASTNode):
    array_name: str = ""
    indices: List[ASTNode] = field(default_factory=list)  # [i], [i, j]


@dataclass
class IfNode(ASTNode):
    condition: ASTNode = None
    then_branch: ASTNode = None
    else_branch: Optional[ASTNode] = None


@dataclass
class WhileNode(ASTNode):
    condition: ASTNode = None
    body: ASTNode = None


@dataclass
class DoWhileNode(ASTNode):
    body: ASTNode = None
    condition: ASTNode = None


@dataclass
class ForNode(ASTNode):
    init: Optional[ASTNode] = None
    condition: Optional[ASTNode] = None
    step: Optional[ASTNode] = None
    body: ASTNode = None


@dataclass
class CaseNode(ASTNode):
    value: Optional[ASTNode] = None  # None for default case
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class SwitchNode(ASTNode):
    expr: ASTNode = None
    cases: List[CaseNode] = field(default_factory=list)


@dataclass
class BreakNode(ASTNode):
    pass


@dataclass
class ContinueNode(ASTNode):
    pass


@dataclass
class ReturnNode(ASTNode):
    expr: Optional[ASTNode] = None


@dataclass
class FunctionCallNode(ASTNode):
    name: str = ""
    arguments: List[ASTNode] = field(default_factory=list)


@dataclass
class FunctionDeclNode(ASTNode):
    return_type: str = "void"
    name: str = ""
    parameters: List[VarDeclNode] = field(default_factory=list)
    body: BlockNode = None
