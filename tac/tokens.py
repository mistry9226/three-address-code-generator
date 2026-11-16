"""
Token definitions and classifications for the TAC Generator.
"""
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Literals
    INTEGER = auto()
    FLOAT = auto()
    IDENTIFIER = auto()
    STRING = auto()

    # Keywords
    INT = auto()
    FLOAT_KW = auto()
    CHAR = auto()
    VOID = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    DO = auto()
    FOR = auto()
    SWITCH = auto()
    CASE = auto()
    DEFAULT = auto()
    BREAK = auto()
    CONTINUE = auto()
    RETURN = auto()

    # Arithmetic Operators
    PLUS = auto()           # +
    MINUS = auto()          # -
    STAR = auto()           # *
    SLASH = auto()          # /
    PERCENT = auto()        # %
    CARET = auto()          # ^

    # Relational Operators
    EQ = auto()             # ==
    NEQ = auto()            # !=
    LT = auto()             # <
    LEQ = auto()            # <=
    GT = auto()             # >
    GEQ = auto()            # >=

    # Logical Operators
    AND = auto()            # &&
    OR = auto()             # ||
    NOT = auto()            # !

    # Assignment Operators
    ASSIGN = auto()         # =
    PLUS_ASSIGN = auto()    # +=
    MINUS_ASSIGN = auto()   # -=
    STAR_ASSIGN = auto()    # *=
    SLASH_ASSIGN = auto()   # /=
    PERCENT_ASSIGN = auto() # %=

    # Increment / Decrement
    INCREMENT = auto()      # ++
    DECREMENT = auto()      # --

    # Punctuation & Delimiters
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACE = auto()         # {
    RBRACE = auto()         # }
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]
    SEMICOLON = auto()      # ;
    COMMA = auto()          # ,
    COLON = auto()          # :
    QUESTION = auto()       # ?

    # Special
    EOF = auto()
    UNKNOWN = auto()


KEYWORDS = {
    'int': TokenType.INT,
    'float': TokenType.FLOAT_KW,
    'char': TokenType.CHAR,
    'void': TokenType.VOID,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'do': TokenType.DO,
    'for': TokenType.FOR,
    'switch': TokenType.SWITCH,
    'case': TokenType.CASE,
    'default': TokenType.DEFAULT,
    'break': TokenType.BREAK,
    'continue': TokenType.CONTINUE,
    'return': TokenType.RETURN,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {repr(self.value)}, L{self.line}:C{self.column})"
