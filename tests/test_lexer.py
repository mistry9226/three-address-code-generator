"""
Tests for Lexical Analysis.
"""
import unittest
from tac.lexer import Lexer, LexerError
from tac.tokens import TokenType


class TestLexer(unittest.TestCase):
    def test_basic_tokens(self):
        source = "int x = 42 + 3.14;"
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens]
        expected = [
            TokenType.INT,
            TokenType.IDENTIFIER,
            TokenType.ASSIGN,
            TokenType.INTEGER,
            TokenType.PLUS,
            TokenType.FLOAT,
            TokenType.SEMICOLON,
            TokenType.EOF
        ]
        self.assertEqual(types, expected)

    def test_comments(self):
        source = """
        // Single line comment
        int a = 10; /* Multi-line
        comment */ int b = 20;
        """
        tokens = Lexer(source).tokenize()
        ids = [t.value for t in tokens if t.type == TokenType.IDENTIFIER]
        self.assertEqual(ids, ['a', 'b'])

    def test_operators(self):
        source = "== != <= >= && || ++ -- += -="
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens[:-1]] # exclude EOF
        expected = [
            TokenType.EQ, TokenType.NEQ, TokenType.LEQ, TokenType.GEQ,
            TokenType.AND, TokenType.OR, TokenType.INCREMENT, TokenType.DECREMENT,
            TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN
        ]
        self.assertEqual(types, expected)

    def test_unterminated_comment(self):
        source = "int a = 5; /* unterminated"
        with self.assertRaises(LexerError):
            Lexer(source).tokenize()


if __name__ == '__main__':
    unittest.main()
