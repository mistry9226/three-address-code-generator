"""
Tests for TAC Code Generation, Quadruples, and Triples.
"""
import unittest
from tac import compile_to_tac


class TestGenerator(unittest.TestCase):
    def test_arithmetic_tac(self):
        source = "x = a + b * c;"
        res = compile_to_tac(source)
        linear = res.linear_tac

        self.assertIn("t1 = b * c", linear)
        self.assertIn("t2 = a + t1", linear)
        self.assertIn("x = t2", linear)

        # Check quadruples count
        self.assertEqual(len(res.quadruples), 3)
        self.assertEqual(res.quadruples[0]['op'], '*')
        self.assertEqual(res.quadruples[1]['op'], '+')
        self.assertEqual(res.quadruples[2]['op'], '=')

        # Check triples
        self.assertEqual(res.triples[0]['op'], '*')
        self.assertEqual(res.triples[1]['op'], '+')
        self.assertEqual(res.triples[1]['arg2'], '(0)')

    def test_if_else_tac(self):
        source = """
        if (a < b) {
            x = 1;
        } else {
            x = 2;
        }
        """
        res = compile_to_tac(source)
        linear = res.linear_tac

        self.assertIn("if a >= b goto L1", linear)
        self.assertIn("x = 1", linear)
        self.assertIn("goto L2", linear)
        self.assertIn("L1:", linear)
        self.assertIn("x = 2", linear)
        self.assertIn("L2:", linear)

    def test_array_2d_tac(self):
        source = """
        int mat[4][5];
        mat[1][2] = 99;
        """
        res = compile_to_tac(source)
        linear = res.linear_tac

        # Row-major: (1 * 5 + 2) * 4
        self.assertIn("t1 = 1 * 5", linear)
        self.assertIn("t2 = t1 + 2", linear)
        self.assertIn("t3 = t2 * 4", linear)
        self.assertIn("mat[t3] = 99", linear)


if __name__ == '__main__':
    unittest.main()
