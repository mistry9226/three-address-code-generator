"""
Three Address Code (TAC) Generator - Main Entry Point.
"""
import sys
import os
import unittest

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    if "--test" in sys.argv:
        print("Running TAC Generator test suite...")
        loader = unittest.TestLoader()
        suite = loader.discover("tests")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    if "--server" in sys.argv:
        from server import run_server
        port = 8000
        for arg in sys.argv[1:]:
            if arg.isdigit():
                port = int(arg)
        run_server(port)
        return

    # Default to CLI
    from cli import main as cli_main
    cli_main()


if __name__ == "__main__":
    main()
