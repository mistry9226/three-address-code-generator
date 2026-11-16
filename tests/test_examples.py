"""
Tests that all example files in examples/ compile to TAC and run without error.
"""
import unittest
import glob
import os
from tac import compile_to_tac, simulate_tac


class TestExamples(unittest.TestCase):
    def test_all_examples_compile(self):
        example_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
        files = sorted(glob.glob(os.path.join(example_dir, "*.c")))
        self.assertGreater(len(files), 0, "No example files found")

        for fpath in files:
            fname = os.path.basename(fpath)
            with self.subTest(example=fname):
                with open(fpath, "r", encoding="utf-8") as f:
                    code = f.read()

                # Compile with optimization
                res = compile_to_tac(code, optimize=True)
                self.assertIsNotNone(res.linear_tac)
                self.assertGreater(len(res.linear_tac), 0)
                self.assertGreater(len(res.quadruples), 0)
                self.assertGreater(len(res.triples), 0)
                self.assertGreater(len(res.indirect_triples), 0)

                # Simulation
                vars_res, logs, trace = simulate_tac(res.tac_instructions)
                self.assertIsInstance(vars_res, dict)


if __name__ == "__main__":
    unittest.main()
