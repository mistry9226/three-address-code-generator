"""
Lexical Analyzer (Scanner) for C-like source code.
"""
from typing import List
from .tokens import Token, TokenType, KEYWORDS


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Lexer Error at line {line}, col {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.pos = 0
        self.line = 1
        self.column = 1

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return '\0'

    def _advance(self) -> str:
        if self.pos >= self.length:
            return '\0'
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _skip_whitespace_and_comments(self):
        while self.pos < self.length:
            ch = self._peek()
            # Whitespace
            if ch in ' \t\r\n':
                self._advance()
                continue

            # Single-line comment //
            if ch == '/' and self._peek(1) == '/':
                self._advance() # /
                self._advance() # /
                while self.pos < self.length and self._peek() != '\n':
                    self._advance()
                continue

            # Multi-line comment /* ... */
            if ch == '/' and self._peek(1) == '*':
                start_line = self.line
                start_col = self.column
                self._advance() # /
                self._advance() # *
                closed = False
                while self.pos < self.length:
                    if self._peek() == '*' and self._peek(1) == '/':
                        self._advance() # *
                        self._advance() # /
                        closed = True
                        break
                    self._advance()
                if not closed:
                    raise LexerError("Unterminated multi-line comment", start_line, start_col)
                continue

            break

    def _scan_number(self) -> Token:
        start_line = self.line
        start_col = self.column
        num_str = ''
        is_float = False

        while self.pos < self.length and (self._peek().isdigit() or self._peek() == '.'):
            if self._peek() == '.':
                if is_float:
                    break  # Second dot not part of number
                # Lookahead to see if next is digit (e.g. 1.5 vs 1.member)
                if not self._peek(1).isdigit():
                    break
                is_float = True
            num_str += self._advance()

        token_type = TokenType.FLOAT if is_float else TokenType.INTEGER
        return Token(token_type, num_str, start_line, start_col)

    def _scan_identifier_or_keyword(self) -> Token:
        start_line = self.line
        start_col = self.column
        text = ''

        while self.pos < self.length and (self._peek().isalnum() or self._peek() == '_'):
            text += self._advance()

        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        return Token(token_type, text, start_line, start_col)

    def _scan_string(self) -> Token:
        start_line = self.line
        start_col = self.column
        quote_char = self._advance()  # Skip opening quote
        text = ''

        while self.pos < self.length and self._peek() != quote_char:
            if self._peek() == '\\':
                self._advance()
                esc = self._advance()
                escape_map = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', '"': '"', "'": "'"}
                text += escape_map.get(esc, esc)
            elif self._peek() == '\n':
                raise LexerError("Unterminated string literal", start_line, start_col)
            else:
                text += self._advance()

        if self.pos >= self.length:
            raise LexerError("Unterminated string literal", start_line, start_col)

        self._advance()  # Skip closing quote
        return Token(TokenType.STRING, text, start_line, start_col)

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.pos < self.length:
            self._skip_whitespace_and_comments()
            if self.pos >= self.length:
                break

            ch = self._peek()
            start_line = self.line
            start_col = self.column

            # Number
            if ch.isdigit():
                tokens.append(self._scan_number())
                continue

            # Identifier or Keyword
            if ch.isalpha() or ch == '_':
                tokens.append(self._scan_identifier_or_keyword())
                continue

            # String literal
            if ch in ('"', "'"):
                tokens.append(self._scan_string())
                continue

            # Two-character operators
            next_ch = self._peek(1)
            two_ch = ch + next_ch

            if two_ch == '==':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.EQ, '==', start_line, start_col))
            elif two_ch == '!=':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.NEQ, '!=', start_line, start_col))
            elif two_ch == '<=':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.LEQ, '<=', start_line, start_col))
            elif two_ch == '>=':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.GEQ, '>=', start_line, start_col))
            elif two_ch == '&&':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.AND, '&&', start_line, start_col))
            elif two_ch == '||':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.OR, '||', start_line, start_col))
            elif two_ch == '++':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.INCREMENT, '++', start_line, start_col))
            elif two_ch == '--':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.DECREMENT, '--', start_line, start_col))
            elif two_ch == '+=':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.PLUS_ASSIGN, '+=', start_line, start_col))
            elif two_ch == '-=':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.MINUS_ASSIGN, '-=', start_line, start_col))
            elif two_ch == '*=':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.STAR_ASSIGN, '*=', start_line, start_col))
            elif two_ch == '/=':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.SLASH_ASSIGN, '/=', start_line, start_col))
            elif two_ch == '%=':
                self._advance(); self._advance()
                tokens.append(Token(TokenType.PERCENT_ASSIGN, '%=', start_line, start_col))
            # Single-character tokens
            elif ch == '+':
                self._advance()
                tokens.append(Token(TokenType.PLUS, '+', start_line, start_col))
            elif ch == '-':
                self._advance()
                tokens.append(Token(TokenType.MINUS, '-', start_line, start_col))
            elif ch == '*':
                self._advance()
                tokens.append(Token(TokenType.STAR, '*', start_line, start_col))
            elif ch == '/':
                self._advance()
                tokens.append(Token(TokenType.SLASH, '/', start_line, start_col))
            elif ch == '%':
                self._advance()
                tokens.append(Token(TokenType.PERCENT, '%', start_line, start_col))
            elif ch == '^':
                self._advance()
                tokens.append(Token(TokenType.CARET, '^', start_line, start_col))
            elif ch == '=':
                self._advance()
                tokens.append(Token(TokenType.ASSIGN, '=', start_line, start_col))
            elif ch == '<':
                self._advance()
                tokens.append(Token(TokenType.LT, '<', start_line, start_col))
            elif ch == '>':
                self._advance()
                tokens.append(Token(TokenType.GT, '>', start_line, start_col))
            elif ch == '!':
                self._advance()
                tokens.append(Token(TokenType.NOT, '!', start_line, start_col))
            elif ch == '(':
                self._advance()
                tokens.append(Token(TokenType.LPAREN, '(', start_line, start_col))
            elif ch == ')':
                self._advance()
                tokens.append(Token(TokenType.RPAREN, ')', start_line, start_col))
            elif ch == '{':
                self._advance()
                tokens.append(Token(TokenType.LBRACE, '{', start_line, start_col))
            elif ch == '}':
                self._advance()
                tokens.append(Token(TokenType.RBRACE, '}', start_line, start_col))
            elif ch == '[':
                self._advance()
                tokens.append(Token(TokenType.LBRACKET, '[', start_line, start_col))
            elif ch == ']':
                self._advance()
                tokens.append(Token(TokenType.RBRACKET, ']', start_line, start_col))
            elif ch == ';':
                self._advance()
                tokens.append(Token(TokenType.SEMICOLON, ';', start_line, start_col))
            elif ch == ',':
                self._advance()
                tokens.append(Token(TokenType.COMMA, ',', start_line, start_col))
            elif ch == ':':
                self._advance()
                tokens.append(Token(TokenType.COLON, ':', start_line, start_col))
            elif ch == '?':
                self._advance()
                tokens.append(Token(TokenType.QUESTION, '?', start_line, start_col))
            else:
                self._advance()
                raise LexerError(f"Unexpected character: {repr(ch)}", start_line, start_col)

        tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return tokens
