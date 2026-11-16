"""
Symbol Table for variable scoping, array dimensions, and types.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Symbol:
    name: str
    type_name: str
    is_array: bool = False
    dimensions: List[int] = field(default_factory=list)
    element_size: int = 4  # Default 4 bytes for 32-bit int/float
    scope_level: int = 0


class SymbolTable:
    def __init__(self, parent: Optional['SymbolTable'] = None, scope_level: int = 0):
        self.parent = parent
        self.scope_level = scope_level
        self.symbols: Dict[str, Symbol] = {}

    def enter_scope(self) -> 'SymbolTable':
        return SymbolTable(parent=self, scope_level=self.scope_level + 1)

    def exit_scope(self) -> Optional['SymbolTable']:
        return self.parent

    def define(self, name: str, type_name: str, dimensions: Optional[List[int]] = None, element_size: int = 4) -> Symbol:
        dims = dimensions or []
        sym = Symbol(
            name=name,
            type_name=type_name,
            is_array=len(dims) > 0,
            dimensions=dims,
            element_size=element_size,
            scope_level=self.scope_level
        )
        self.symbols[name] = sym
        return sym

    def lookup(self, name: str) -> Optional[Symbol]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def get_all_symbols(self) -> Dict[str, Symbol]:
        all_syms = {}
        if self.parent:
            all_syms.update(self.parent.get_all_symbols())
        all_syms.update(self.symbols)
        return all_syms
