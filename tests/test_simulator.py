"""
Tests for TAC Virtual Machine / Simulator.
"""
import unittest
from tac import compile_to_tac, simulate_tac


class TestSimulator(unittest.TestCase):
    def test_arithmetic_simulation(self):
        source = """
        int a = 10;
        int b = 20;
        int c = a * b + 5;
        """
        res = compile_to_tac(source)
        vars_res, logs, trace = simulate_tac(res.tac_instructions)

        self.assertEqual(vars_res.get('a'), 10)
        self.assertEqual(vars_res.get('b'), 20)
        self.assertEqual(vars_res.get('c'), 205)

    def test_loop_simulation(self):
        source = """
        int i = 1;
        int sum = 0;
        while (i <= 5) {
            sum += i;
            i++;
        }
        """
        res = compile_to_tac(source)
        vars_res, logs, trace = simulate_tac(res.tac_instructions)

        self.assertEqual(vars_res.get('sum'), 15)
        self.assertEqual(vars_res.get('i'), 6)


if __name__ == '__main__':
    unittest.main()
