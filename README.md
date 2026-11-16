# ⚡ Three Address Code (TAC) Generator

A comprehensive, academic-grade **Compiler Design** project implementing an Intermediate Code Generator for a C-like programming language. It performs Lexical Analysis, Syntax Analysis, AST generation, Syntax-Directed Translation (SDT) into **Three Address Code (TAC)**, **Quadruples**, **Triples**, **Indirect Triples**, **Control Flow Graphs (CFG)**, **TAC Optimization**, and includes an integrated **TAC Virtual Machine / Simulator**.

Features both a **Rich Terminal CLI** and a **Web GUI Workbench**.

---

## 📌 Features

- **Lexical Analysis (Scanner)**: Tokenizes identifiers, keywords, literals (int, float, string), comments (`//` and `/* ... */`), relational, logical, arithmetic, and assignment operators.
- **Syntax Analysis (Parser)**: Recursive-descent parser with operator precedence climbing, generating an Abstract Syntax Tree (AST).
- **Intermediate Code Generation (SDT)**:
  - Arithmetic Expressions (`+`, `-`, `*`, `/`, `%`, `^`, unary minus `-`)
  - Relational & Logical Expressions (`<`, `<=`, `>`, `>=`, `==`, `!=`, `&&`, `||`, `!`)
  - Control Flow Statements:
    - `if (condition) { ... } else { ... }`
    - `while (condition) { ... }`
    - `do { ... } while (condition);`
    - `for (init; condition; step) { ... }`
    - `switch (expr) { case ...: ... break; default: ... }`
    - `break;` and `continue;`
  - Array Address Translation:
    - **1D Array Access**: `base + (i * element_size)`
    - **2D Array Access (Row-Major)**: `base + ((i * N + j) * element_size)`
  - Function definitions, parameter passing (`param`), call (`call`), and return (`return`).
- **Intermediate Representations**:
  - **Linear TAC**: Human-readable instruction stream with labels.
  - **Quadruples**: Records of `(op, arg1, arg2, result)`.
  - **Triples**: Records of `(op, arg1, arg2)` referencing instruction positions `(index)`.
  - **Indirect Triples**: Pointer list `[0], [1]...` referencing the Triples array.
- **Control Flow Graph (CFG) & Basic Blocks**:
  - Dragon Book leader identification algorithm.
  - Partitioning into Basic Blocks ($B_1, B_2, \dots$).
  - Generation of Mermaid flowchart diagrams and ASCII block graphs.
- **TAC Optimizer**:
  - Constant Folding (`3 + 4 * 2` $\rightarrow$ `11`)
  - Algebraic Simplifications (`x + 0` $\rightarrow$ `x`, `x * 1` $\rightarrow$ `x`, `x * 0` $\rightarrow$ `0`, `x / 1` $\rightarrow$ `x`)
  - Copy Propagation (`t1 = a; b = t1 + c` $\rightarrow$ `b = a + c`)
  - Dead Code Elimination (unreachable code after unconditional `goto`, unused temporaries).
- **TAC Virtual Machine / Simulator**:
  - Simulates the execution of generated TAC instructions step-by-step.
  - Variable memory inspector and execution trace.
- **Interactive Interfaces**:
  - **Modern Web GUI**: Live editor, tabbed views, Mermaid CFG diagram, side-by-side optimization diff, and step-by-step VM debugger.
  - **Rich CLI**: Formatted colored tables, AST tree visualization, and interactive REPL.

---

## 🏗️ Project Architecture

```
tac-generator/
├── tac/
│   ├── __init__.py           # Package interface & compile_to_tac() pipeline
│   ├── tokens.py             # Token specifications and TokenType enum
│   ├── lexer.py              # Lexical scanner with comment & line tracking
│   ├── ast_nodes.py          # AST Node definitions (Visitor pattern, to_dict)
│   ├── parser.py             # Recursive descent parser with operator precedence
│   ├── symbol_table.py       # Scoped symbol table for variables and array dimensions
│   ├── tac_instruction.py    # Instruction classes: Linear, Quadruple, Triple, Indirect
│   ├── generator.py          # Intermediate Code Generator (SDT rules)
│   ├── optimizer.py          # Constant folding, propagation, dead code elimination
│   ├── cfg.py                # Dragon Book Basic Block partitioning & CFG
│   └── simulator.py          # Virtual Machine / Interpreter for TAC execution
├── web/
│   ├── index.html            # Workbench UI (Editor, Tabs, Tables, Visualizer)
│   ├── style.css             # Dark IDE styling
│   └── app.js                # Frontend controller & Mermaid renderer
├── examples/
│   ├── 01_arithmetic.c       # Precedence and subexpressions
│   ├── 02_if_else.c          # Conditional branching and logical operators
│   ├── 03_while_loop.c       # While loop and accumulator
│   ├── 04_for_loop.c         # For loop with break and continue
│   ├── 05_array_1d_2d.c      # Row-major 1D & 2D array calculations
│   ├── 06_switch_case.c      # Multi-way branching
│   ├── 07_functions.c        # Function definitions, params, call, return
│   └── 08_optimization.c    # Optimizable code patterns
├── tests/
│   ├── test_lexer.py         # Unit tests for scanner
│   ├── test_parser.py        # Unit tests for AST construction
│   ├── test_generator.py     # Unit tests for TAC, Quads, Triples
│   ├── test_optimizer.py     # Unit tests for optimization passes
│   └── test_simulator.py     # Unit tests for VM simulation
├── cli.py                    # Terminal interface with Rich formatting
├── server.py                 # Built-in zero-dependency HTTP server
├── main.py                   # Master entry point
└── README.md                 # Complete documentation
```

---

## 📚 Theory: Intermediate Representations

### 1. Three Address Code (TAC)
An intermediate code representation where each instruction has at most one operator on the right-hand side and at most three address references (two operands and one result).

$$\text{result} = \text{arg}_1 \text{ op } \text{arg}_2$$

### 2. Quadruples vs. Triples vs. Indirect Triples

| Feature | Quadruples | Triples | Indirect Triples |
| :--- | :--- | :--- | :--- |
| **Record Format** | `(op, arg1, arg2, result)` | `(op, arg1, arg2)` | Pointer array $\to$ Triples table |
| **Temporary Variables** | Explicitly named (`t1`, `t2`, ...) | Implicit via position `(0)`, `(1)` | Implicit via position `(0)`, `(1)` |
| **Optimization Friendly** | Easy to move instructions | Hard to reorder (indices change) | **Very easy** (only swap pointers) |
| **Space Complexity** | 4 fields per instruction | 3 fields per instruction | 3 fields + 1 pointer |

---

## 📖 Syntax-Directed Translation (SDT) Rules

### Arithmetic & Assignment
- $E \to E_1 + E_2$:
  $$\begin{aligned}
  E.\text{addr} &= \text{new\_temp}() \\
  \text{emit}(E.\text{addr} &= E_1.\text{addr} + E_2.\text{addr})
  \end{aligned}$$
- $S \to \text{id} = E$:
  $$\text{emit}(\text{id}.\text{name} = E.\text{addr})$$

### Multi-Dimensional Arrays (Row-Major)
For 2D array $A[N][M]$ with element width $w$:
$$\text{Offset} = (i \times M + j) \times w$$
Generated TAC:
```
t1 = i * M
t2 = t1 + j
t3 = t2 * w
matrix[t3] = val
```

### Control Flow (While Loop)
- $S \to \mathbf{while} \, (E) \, S_1$:
  $$\begin{aligned}
  L_{\text{start}} &= \text{new\_label}() \\
  L_{\text{end}} &= \text{new\_label}() \\
  &\text{emit}(L_{\text{start}}:) \\
  &\text{emit}(\mathbf{ifFalse} \, E.\text{addr} \, \mathbf{goto} \, L_{\text{end}}) \\
  &\text{code for } S_1 \\
  &\text{emit}(\mathbf{goto} \, L_{\text{start}}) \\
  &\text{emit}(L_{\text{end}}:)
  \end{aligned}$$

---

## 🚀 How to Run

### 1. Run All Tests
```bash
python main.py --test
```

### 2. Compile a Source File via CLI
```bash
# Basic compilation (Linear TAC)
python cli.py examples/01_arithmetic.c

# Show all representations (AST, Quadruples, Triples, Indirect Triples, CFG, Optimizer, Run)
python cli.py examples/01_arithmetic.c --all

# Show Quadruples and Triples tables
python cli.py examples/05_array_1d_2d.c --tables

# Show Control Flow Graph (CFG)
python cli.py examples/02_if_else.c --cfg

# Run optimization pass
python cli.py examples/08_optimization.c -O

# Execute generated TAC via the Simulator
python cli.py examples/03_while_loop.c --run
```

### 3. Interactive REPL Mode
```bash
python cli.py --repl
```
Type expressions or statements directly:
```
tac> int a = 10; int b = 20; int c = a + b * 2;
```

### 4. Launch the Interactive Web Workbench
```bash
python server.py
# Or:
python cli.py --gui
```
Then open your browser at **`http://localhost:8000`**.

---

## 📊 Example Outputs

### Input Code (`01_arithmetic.c`)
```c
b = 10;
c = 5;
d = 2;
e = 20;
f = 4;
result = b + c * d - (e / f) + (b ^ 2);
```

### Generated Linear TAC
```python
b = 10
c = 5
d = 2
e = 20
f = 4
t1 = c * d
t2 = b + t1
t3 = e / f
t4 = t2 - t3
t5 = b ^ 2
t6 = t4 + t5
result = t6
```

### Generated Quadruples Table
| # | Operator (op) | Arg 1 | Arg 2 | Result |
|---|---------------|-------|-------|--------|
| 0 | = | 10 | | b |
| 1 | = | 5 | | c |
| 2 | = | 2 | | d |
| 3 | = | 20 | | e |
| 4 | = | 4 | | f |
| 5 | * | c | d | t1 |
| 6 | + | b | t1 | t2 |
| 7 | / | e | f | t3 |
| 8 | - | t2 | t3 | t4 |
| 9 | ^ | b | 2 | t5 |
| 10 | + | t4 | t5 | t6 |
| 11 | = | t6 | | result |

### Generated Triples Table
| Index | Operator | Arg 1 | Arg 2 |
|---|---|---|---|
| (5) | * | c | d |
| (6) | + | b | (5) |
| (7) | / | e | f |
| (8) | - | (6) | (7) |
| (9) | ^ | b | 2 |
| (10) | + | (8) | (9) |
| (11) | = | result | (10) |

### Virtual Machine Output
```
Final Variable Values in Memory:
  b = 10
  c = 5
  d = 2
  e = 20
  f = 4
  result = 115
Total steps: 12
```

---

## 🎓 Academic Curriculum Relevance

This project directly aligns with:
- **CS / IT Engineering Compiler Design Syllabi** (ABET, AICTE, ACM/IEEE curriculum).
- **Textbook References**:
  - *Compilers: Principles, Techniques, and Tools* (Aho, Lam, Sethi, Ullman - The Dragon Book) - Chapters 6, 8, 9.
  - *Engineering a Compiler* (Cooper & Torczon).
