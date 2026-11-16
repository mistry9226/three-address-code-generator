"""
Tests for Parser and AST generation.
"""
import unittest
from tac.lexer import Lexer
from tac.parser import Parser
from tac.ast_nodes import ProgramNode, VarDeclNode, AssignNode, BinaryOpNode, IfNode, WhileNode


class TestParser(unittest.TestCase):
    def test_expression_precedence(self):
        source = "int x = a + b * c;"
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()

        self.assertIsInstance(ast, ProgramNode)
        self.assertEqual(len(ast.statements), 1)
        decl = ast.statements[0]
        self.assertIsInstance(decl, VarDeclNode)
        init = decl.declarators[0].init_value
        self.assertIsInstance(init, BinaryOpNode)
        self.assertEqual(init.op, '+')
        self.assertIsInstance(init.right, BinaryOpNode)
        self.assertEqual(init.right.op, '*')

    def test_control_flow_parsing(self):
        source = "if (x > 0) { y = 1; } else { y = 0; }"
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()

        self.assertEqual(len(ast.statements), 1)
        if_node = ast.statements[0]
        self.assertIsInstance(if_node, IfNode)
        self.assertIsNotNone(if_node.else_branch)

    def test_loop_parsing(self):
        source = "while (i < 10) { i++; }"
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()

        self.assertEqual(len(ast.statements), 1)
        while_node = ast.statements[0]
        self.assertIsInstance(while_node, WhileNode)


if __name__ == '__main__':
    unittest.main()
