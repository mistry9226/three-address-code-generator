"""
Tests for TAC Optimizer.
"""
import unittest
from tac import compile_to_tac


class TestOptimizer(unittest.TestCase):
    def test_constant_folding(self):
        source = "x = 3 + 4 * 2;"
        res = compile_to_tac(source, optimize=True)

        self.assertIsNotNone(res.optimized_linear_tac)
        # Constant folding should simplify 4*2=8, then 3+8=11
        self.assertIn("11", res.optimized_linear_tac)
        self.assertGreater(res.optimizer_stats['constant_folds'], 0)

    def test_algebraic_identities(self):
        source = """
        y = a + 0;
        z = b * 1;
        w = c * 0;
        """
        res = compile_to_tac(source, optimize=True)
        opt_linear = res.optimized_linear_tac

        self.assertIn("y = a", opt_linear)
        self.assertIn("z = b", opt_linear)
        self.assertIn("w = 0", opt_linear)


if __name__ == '__main__':
    unittest.main()
