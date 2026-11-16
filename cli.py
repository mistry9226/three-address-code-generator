"""
Command Line Interface (CLI) for the Three Address Code (TAC) Generator.
Supports rich formatted tables, AST trees, CFG display, optimization metrics, and REPL.
"""
import argparse
import sys
import os
import webbrowser
from typing import Optional

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tac import compile_to_tac, simulate_tac, CompilationResult
from tac.tac_instruction import TACInstruction

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    from rich.syntax import Syntax
    from rich.columns import Columns
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


def print_banner():
    if RICH_AVAILABLE:
        console.print(Panel.fit(
            "[bold cyan]⚡ THREE ADDRESS CODE (TAC) GENERATOR ⚡[/bold cyan]\n"
            "[dim]Compiler Design Project | Lexer, Parser, SDT, Quadruples, Triples, CFG & VM[/dim]",
            border_style="cyan"
        ))
    else:
        print("=" * 60)
        print("THREE ADDRESS CODE (TAC) GENERATOR - COMPILER DESIGN")
        print("=" * 60)


def display_ast(ast_dict: dict, label: str = "Abstract Syntax Tree"):
    if not RICH_AVAILABLE:
        import pprint
        print(f"\n--- {label} ---")
        pprint.pprint(ast_dict)
        return

    tree = Tree(f"[bold green]🌳 {label}[/bold green]")

    def build_tree(data: dict, current_node):
        node_type = data.get('type', 'Node')
        branch = current_node.add(f"[bold yellow]{node_type}[/bold yellow]")
        for k, v in data.items():
            if k == 'type':
                continue
            if isinstance(v, dict):
                build_tree(v, branch.add(f"[cyan]{k}[/cyan]"))
            elif isinstance(v, list):
                if not v:
                    continue
                list_branch = branch.add(f"[cyan]{k}[/cyan] ({len(v)})")
                for item in v:
                    if isinstance(item, dict):
                        build_tree(item, list_branch)
                    else:
                        list_branch.add(f"[dim]{str(item)}[/dim]")
            else:
                branch.add(f"[cyan]{k}[/cyan]: [magenta]{repr(v)}[/magenta]")

    build_tree(ast_dict, tree)
    console.print(tree)


def display_linear_tac(linear_code: str, title: str = "Three Address Code (Linear)"):
    if RICH_AVAILABLE:
        syntax = Syntax(linear_code, "python", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"[bold green]{title}[/bold green]", border_style="green"))
    else:
        print(f"\n--- {title} ---")
        for i, line in enumerate(linear_code.splitlines(), 1):
            print(f"{i:3d} | {line}")


def display_quadruples(quadruples: list):
    if RICH_AVAILABLE:
        table = Table(title="[bold blue]Quadruples Representation (op, arg1, arg2, result)[/bold blue]", border_style="blue")
        table.add_column("#", style="dim", width=4)
        table.add_column("Operator (op)", style="bold yellow")
        table.add_column("Argument 1 (arg1)", style="cyan")
        table.add_column("Argument 2 (arg2)", style="magenta")
        table.add_column("Result (result)", style="bold green")

        for q in quadruples:
            table.add_row(str(q['index']), q['op'], q['arg1'], q['arg2'], q['result'])
        console.print(table)
    else:
        print("\n--- Quadruples Table ---")
        print(f"{'#':<4} | {'Operator':<12} | {'Arg 1':<12} | {'Arg 2':<12} | {'Result':<12}")
        print("-" * 60)
        for q in quadruples:
            print(f"{q['index']:<4} | {q['op']:<12} | {q['arg1']:<12} | {q['arg2']:<12} | {q['result']:<12}")


def display_triples(triples: list):
    if RICH_AVAILABLE:
        table = Table(title="[bold magenta]Triples Representation (op, arg1, arg2)[/bold magenta]", border_style="magenta")
        table.add_column("Index", style="dim", width=8)
        table.add_column("Operator (op)", style="bold yellow")
        table.add_column("Argument 1 (arg1)", style="cyan")
        table.add_column("Argument 2 (arg2)", style="magenta")

        for t in triples:
            table.add_row(t['index'], t['op'], t['arg1'], t['arg2'])
        console.print(table)
    else:
        print("\n--- Triples Table ---")
        print(f"{'Index':<8} | {'Operator':<12} | {'Arg 1':<12} | {'Arg 2':<12}")
        print("-" * 50)
        for t in triples:
            print(f"{t['index']:<8} | {t['op']:<12} | {t['arg1']:<12} | {t['arg2']:<12}")


def display_indirect_triples(indirect: list):
    if RICH_AVAILABLE:
        table = Table(title="[bold cyan]Indirect Triples Representation[/bold cyan]", border_style="cyan")
        table.add_column("Pointer", style="bold yellow", width=10)
        table.add_column("Triple Index", style="dim", width=14)
        table.add_column("Operator", style="cyan")
        table.add_column("Arg 1", style="magenta")
        table.add_column("Arg 2", style="green")

        for ind in indirect:
            table.add_row(ind['pointer'], ind['statement'], ind['op'], ind['arg1'], ind['arg2'])
        console.print(table)
    else:
        print("\n--- Indirect Triples Table ---")
        print(f"{'Pointer':<10} | {'Triple Index':<14} | {'Operator':<10} | {'Arg 1':<10} | {'Arg 2':<10}")
        print("-" * 60)
        for ind in indirect:
            print(f"{ind['pointer']:<10} | {ind['statement']:<14} | {ind['op']:<10} | {ind['arg1']:<10} | {ind['arg2']:<10}")


def display_cfg(cfg):
    if RICH_AVAILABLE:
        console.print("\n[bold yellow]🔄 Basic Blocks & Control Flow Graph (CFG)[/bold yellow]")
        for b in cfg.blocks:
            body = "\n".join(i.to_linear() for i in b.instructions)
            preds = ", ".join(p.name for p in b.predecessors) or "None"
            succs = ", ".join(s.name for s in b.successors) or "None"
            footer = f"[dim]Preds: [{preds}] | Succs: [{succs}][/dim]"
            console.print(Panel(f"{body}\n\n{footer}", title=f"[bold green]Block {b.name}[/bold green]", border_style="green"))
    else:
        print("\n--- Basic Blocks & CFG ---")
        for b in cfg.blocks:
            print(b.to_linear())
            preds = ", ".join(p.name for p in b.predecessors) or "None"
            succs = ", ".join(s.name for s in b.successors) or "None"
            print(f"  Predecessors: {preds} | Successors: {succs}\n")


def display_simulation(instructions: list):
    user_vars, logs, trace = simulate_tac(instructions)

    if RICH_AVAILABLE:
        console.print("\n[bold green]🚀 TAC Virtual Machine / Simulator Results[/bold green]")
        if logs:
            console.print(Panel("\n".join(logs), title="[bold cyan]Standard Output Logs[/bold cyan]", border_style="cyan"))

        table = Table(title="[bold yellow]Final Variable Values in Memory[/bold yellow]", border_style="yellow")
        table.add_column("Variable", style="bold cyan")
        table.add_column("Value", style="bold green")

        for k, v in sorted(user_vars.items()):
            table.add_row(k, str(v))
        console.print(table)
        console.print(f"[dim]Total instructions executed: {len(trace)} steps[/dim]\n")
    else:
        print("\n--- Simulation Output ---")
        for log in logs:
            print(log)
        print("\nVariables:")
        for k, v in sorted(user_vars.items()):
            print(f"  {k} = {v}")
        print(f"Total steps: {len(trace)}")


def run_repl():
    print_banner()
    if RICH_AVAILABLE:
        console.print("[dim]Type source code statements. Press Enter on empty line to compile. Type 'exit' to quit.[/dim]\n")
    else:
        print("Type source code statements. Press Enter on empty line to compile. Type 'exit' to quit.\n")

    while True:
        lines = []
        try:
            prompt = "tac> "
            while True:
                line = input(prompt)
                if line.strip().lower() == 'exit':
                    return
                if not line.strip() and lines:
                    break
                lines.append(line)
                prompt = "...  "
        except (EOFError, KeyboardInterrupt):
            break

        source = "\n".join(lines).strip()
        if not source:
            continue

        try:
            res = compile_to_tac(source, optimize=True)
            display_linear_tac(res.linear_tac)
            display_quadruples(res.quadruples)
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[bold red]Error:[/bold red] {e}")
            else:
                print(f"Error: {e}")


def export_report(result: CompilationResult, output_path: str, stats=None, sim_vars=None):
    """Exports full compilation details into a formatted Markdown report file."""
    lines = [
        "# Compiler Design - Three Address Code Generation Report",
        "",
        "## 1. Source Code",
        "```c",
        result.source.strip(),
        "```",
        "",
        "## 2. Linear Three Address Code (TAC)",
        "```python",
        result.linear_tac.strip(),
        "```",
        "",
        "## 3. Quadruples Table",
        "| # | Op | Arg 1 | Arg 2 | Result |",
        "|---|----|-------|-------|--------|"
    ]
    for q in result.quadruples:
        lines.append(f"| {q['index']} | `{q['op']}` | {q['arg1']} | {q['arg2']} | **{q['result']}** |")

    lines.extend([
        "",
        "## 4. Triples Table",
        "| Index | Op | Arg 1 | Arg 2 |",
        "|-------|----|-------|-------|"
    ])
    for t in result.triples:
        lines.append(f"| {t['index']} | `{t['op']}` | {t['arg1']} | {t['arg2']} |")

    lines.extend([
        "",
        "## 5. Indirect Triples Table",
        "| Pointer | Triple Index | Op | Arg 1 | Arg 2 |",
        "|---------|--------------|----|-------|-------|"
    ])
    for ind in result.indirect_triples:
        lines.append(f"| {ind['pointer']} | {ind['statement']} | `{ind['op']}` | {ind['arg1']} | {ind['arg2']} |")

    if result.optimized_linear_tac:
        lines.extend([
            "",
            "## 6. Optimized Three Address Code",
            "```python",
            result.optimized_linear_tac.strip(),
            "```"
        ])
        if stats:
            lines.extend([
                "",
                "### Optimization Metrics",
                f"- **Initial Instructions**: {stats['initial_count']}",
                f"- **Final Instructions**: {stats['final_count']}",
                f"- **Instructions Reduced**: {stats['instructions_reduced']}",
                f"- **Constant Folds**: {stats['constant_folds']}",
                f"- **Algebraic Simplifications**: {stats['algebraic_simplifications']}",
                f"- **Copy Propagations**: {stats['copy_propagations']}",
                f"- **Dead Code Eliminated**: {stats['dead_instructions_removed']}"
            ])

    if sim_vars:
        lines.extend([
            "",
            "## 7. Virtual Machine Execution State",
            "| Variable | Value |",
            "|----------|-------|"
        ])
        for k, v in sorted(sim_vars.items()):
            lines.append(f"| `{k}` | `{v}` |")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if RICH_AVAILABLE:
        console.print(f"[bold green]✓ Report exported successfully to:[/bold green] {output_path}")
    else:
        print(f"Report exported successfully to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Three Address Code (TAC) Generator - Compiler Design Project")
    parser.add_argument("file", nargs="?", help="Path to source code file (.c or text)")
    parser.add_argument("-e", "--expr", help="Direct source code string to compile")
    parser.add_argument("--ast", action="store_true", help="Display Abstract Syntax Tree")
    parser.add_argument("--tables", action="store_true", help="Display Quadruples, Triples, and Indirect Triples")
    parser.add_argument("--cfg", action="store_true", help="Display Basic Blocks and Control Flow Graph")
    parser.add_argument("-O", "--optimize", action="store_true", help="Run TAC optimization passes")
    parser.add_argument("--run", action="store_true", help="Execute TAC via the built-in Virtual Machine Simulator")
    parser.add_argument("--all", action="store_true", help="Show all representations (AST, TAC, Tables, CFG, Optimization, Run)")
    parser.add_argument("--export", help="Export full compilation report to a markdown file (e.g. report.md)")
    parser.add_argument("--repl", action="store_true", help="Start interactive REPL mode")
    parser.add_argument("--gui", action="store_true", help="Launch the local interactive Web GUI")

    args = parser.parse_args()

    if args.gui:
        import subprocess
        server_path = os.path.join(os.path.dirname(__file__), "server.py")
        print("Starting TAC Generator Interactive Web UI...")
        try:
            from server import run_server
            webbrowser.open("http://localhost:8000")
            run_server(port=8000)
        except Exception as e:
            print(f"Could not launch server: {e}")
        return

    if args.repl or (not args.file and not args.expr):
        run_repl()
        return

    source = ""
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            source = f.read()
    elif args.expr:
        source = args.expr

    print_banner()

    try:
        res = compile_to_tac(source, optimize=args.optimize or args.all)

        display_linear_tac(res.linear_tac)

        if args.ast or args.all:
            display_ast(res.ast.to_dict())

        if args.tables or args.all:
            display_quadruples(res.quadruples)
            display_triples(res.triples)
            display_indirect_triples(res.indirect_triples)

        if args.cfg or args.all:
            display_cfg(res.cfg)

        if (args.optimize or args.all) and res.optimized_linear_tac:
            display_linear_tac(res.optimized_linear_tac, title="Optimized Three Address Code")
            if RICH_AVAILABLE:
                stats = res.optimizer_stats
                console.print(Panel(
                    f"Initial Instructions: [bold]{stats['initial_count']}[/bold]\n"
                    f"Final Instructions:   [bold green]{stats['final_count']}[/bold green]\n"
                    f"Instructions Saved:   [bold cyan]{stats['instructions_reduced']}[/bold cyan]\n"
                    f"Constant Folds:       [bold yellow]{stats['constant_folds']}[/bold yellow]\n"
                    f"Algebraic Reductions: [bold magenta]{stats['algebraic_simplifications']}[/bold magenta]\n"
                    f"Copy Propagations:    [bold blue]{stats['copy_propagations']}[/bold blue]\n"
                    f"Dead Code Removed:    [bold red]{stats['dead_instructions_removed']}[/bold red]",
                    title="[bold yellow]⚡ Optimization Statistics[/bold yellow]",
                    border_style="yellow"
                ))

        sim_vars = None
        if args.run or args.all or args.export:
            target_instrs = res.optimized_instructions if (args.optimize and res.optimized_instructions) else res.tac_instructions
            if args.run or args.all:
                display_simulation(target_instrs)
            if args.export:
                sim_vars, _, _ = simulate_tac(target_instrs)

        if args.export:
            export_report(res, args.export, stats=res.optimizer_stats, sim_vars=sim_vars)

    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[bold red]Compilation Failed:[/bold red] {e}")
        else:
            print(f"Compilation Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
