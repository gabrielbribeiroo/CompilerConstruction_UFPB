# CompilerConstruction_UFPB

Repository for the assignments of the **Compiler Construction 1** course,
Computer Science program at the Federal University of Paraíba (UFPB),
semester 2026.1.

- **Professor:** Andrei de Araújo Formiga
- **Term:** P6 - 2026.1

Across assignments 02 through 10 we build a small compiler step by step,
finishing with complete compilers for the **EC1**/**EC2**/**EV**/**Cmd**/**Fun**
languages (Constant Expressions 1/2, Expressions with Variables,
Commands, Functions): a lexer (04), a recursive-descent parser plus tree-walking
interpreter (05), an x86-64 code generator (06) that ties everything
together, a precedence/associativity-aware parser (07) that lets
expressions be written without mandatory parentheses, variable
declarations plus a semantic-analysis pass with a symbol table (08),
conditionals/loops/comparison operators (09) — making Cmd the
first Turing-complete language in this series — and function
declarations with parameters, local variables and (direct) recursion
(10), using a stack-based calling convention with `CALL`/`RET` and a
frame pointer. Assignment 02 was a warm-up compiler for integer
constants, and Assignment 03 was a hand-written assembly exercise
(Zeller's Congruence) that informed the codegen scheme used in
Assignment 06.

## Authors

| [<img src="https://github.com/davialves1820.png?size=100" width=100><br><sub>Davi Alves Rodrigues</sub>](https://github.com/davialves1820) | [<img src="https://github.com/gabrielbribeiroo.png?size=100" width=100><br><sub>Gabriel Ribeiro</sub>](https://github.com/gabrielbribeiroo) | [<img src="https://github.com/JoaoVitorSampaio.png?size=100" width=100><br><sub>João Vitor Sampaio</sub>](https://github.com/JoaoVitorSampaio) | [<img src="https://github.com/Nathanmn2004.png?size=100" width=100><br><sub>Nathan Meira Nobrega</sub>](https://github.com/Nathanmn2004) |
| :---: | :---: | :---: | :---: |

## Assignments

| #  | Topic                                            | Directory                                            | Status    |
| -- | ------------------------------------------------ | ---------------------------------------------------- | --------- |
| 02 | CI Compiler — Integer Constants                  | [`compilador-ci/`](./compilador-ci)                  | Delivered |
| 03 | Zeller's Congruence — hand-written assembly      | [`congruencia-zeller/`](./congruencia-zeller)        | Delivered |
| 04 | EC1 — Lexical Analysis                           | [`expressoes-constantes/`](./expressoes-constantes)  | Delivered |
| 05 | EC1 — Recursive-Descent Parser + Interpreter     | [`analise-sintatica-ec1/`](./analise-sintatica-ec1)  | Delivered |
| 06 | EC1 — Full Compiler (x86-64 Code Generation)     | [`compilador-ec1/`](./compilador-ec1)                | Delivered |
| 07 | EC2 — Precedence & Associativity                 | [`compilador-ec2/`](./compilador-ec2)                | Delivered |
| 08 | EV — Variables & Semantic Analysis               | [`compilador-ev/`](./compilador-ev)                  | Delivered |
| 09 | Cmd — Conditionals, Loops & Comparisons (Turing-complete) | [`compilador-cmd/`](./compilador-cmd)       | Delivered |
| 10 | Fun — Functions (params, locals, direct recursion)        | [`compilador-fun/`](./compilador-fun)       | Delivered |

Each subdirectory contains the assignment's source code, a `README.md` with
usage instructions, and a `RELATORIO.md` (report) describing the work.

## Layout

```
CompilerConstruction_UFPB/
├── README.md                # this file
├── .gitignore
├── compilador-ci/           # Assignment 02 - CI Compiler
│   ├── compci.py
│   ├── runtime.s
│   ├── README.md
│   ├── RELATORIO.md
│   └── testes/
│       ├── p1.ci
│       └── erro.ci
├── congruencia-zeller/      # Assignment 03 - Zeller's Congruence
│   ├── zeller.asm
│   ├── zeller.c
│   └── parte2_respostas.md
├── expressoes-constantes/   # Assignment 04 - Constant Expressions 1 (Lexer)
│   ├── lexer.py
│   ├── test lexer.py
│   ├── README.md
│   ├── RELATORIO.md
│   └── PLANO.md
├── analise-sintatica-ec1/   # Assignment 05 - Constant Expressions 1 (Parser + Interpreter)
│   ├── lexer.py
│   ├── ast_ec1.py
│   ├── parser.py
│   ├── ec1.py
│   ├── exemplos/
│   ├── tests/test_parser.py
│   ├── README.md
│   ├── PLANO.md
│   └── RELATORIO.md
├── compilador-ec1/          # Assignment 06 - Constant Expressions 1 (Full Compiler)
│   ├── lexer.py
│   ├── ast_ec1.py
│   ├── parser.py
│   ├── codegen.py
│   ├── compec1.py
│   ├── runtime.s
│   ├── exemplos/
│   ├── tests/test_codegen.py
│   ├── README.md
│   ├── PLANO.md
│   └── RELATORIO.md
├── compilador-ec2/          # Assignment 07 - Constant Expressions 2 (Precedence)
│   ├── lexer.py             # identical to Assignment 06
│   ├── ast_ec1.py           # identical to Assignment 06
│   ├── parser.py            # NEW: exp_a / exp_m / prim grammar
│   ├── codegen.py           # identical to Assignment 06
│   ├── compec2.py
│   ├── runtime.s            # identical to Assignment 06
│   ├── exemplos/
│   ├── tests/test_parser_precedencia.py
│   ├── README.md
│   ├── PLANO.md
│   └── RELATORIO.md
├── compilador-ev/           # Assignment 08 - Expressions with Variables
│   ├── lexer.py             # extended: IDENT, IGUAL, PONTO_VIRGULA
│   ├── ast_ev.py            # Exp, Const, OpBin, Op, Var, Decl, Programa
│   ├── parser.py            # programa / decl / exp / exp_m / prim
│   ├── semantica.py         # symbol table + variable-use checking
│   ├── codegen.py           # extended: .bss section, load/store variables
│   ├── compev.py
│   ├── runtime.s            # identical to Assignment 06
│   ├── exemplos/
│   ├── tests/test_ev.py
│   ├── README.md
│   ├── PLANO.md
│   └── RELATORIO.md
├── compilador-cmd/          # Assignment 09 - Commands (Turing-complete)
│   ├── lexer.py             # extended: {, }, <, >, ==, if/else/while/return
│   ├── ast_cmd.py           # Exp/Const/Var/OpBin/Op + Atrib/If/While/Programa
│   ├── parser.py            # programa / cmd / if / while / atrib / exp (comparison) / exp_a / exp_m / prim
│   ├── semantica.py         # extended: assignment-target + RHS checking, recursive over cmds
│   ├── codegen.py           # extended: comparisons (cmp+setz/setl/setg), if/while via labels + jz/jmp
│   ├── compcmd.py
│   ├── runtime.s            # identical to Assignment 06
│   ├── exemplos/
│   ├── tests/test_cmd.py
│   ├── README.md
│   ├── PLANO.md
│   └── RELATORIO.md
└── compilador-fun/          # Assignment 10 - Functions
    ├── lexer.py             # extended: comma, fun/var/main
    ├── ast_fun.py           # Exp/Const/Var/OpBin/Chamada + Cmd/Atrib/If/While + VarDecl/FunDecl/Programa
    ├── parser.py            # decl (vardecl|fundecl) / params / args / call-vs-var lookahead
    ├── semantica.py         # symbol table with globals + functions, lexical scoping
    ├── codegen.py           # calling convention: push/call/cleanup, prologue/epilogue via %rbp
    ├── compfun.py
    ├── runtime.s            # identical to Assignment 06
    ├── exemplos/
    ├── tests/test_fun.py
    ├── README.md
    ├── PLANO.md
    └── RELATORIO.md
```

## Quick start

Each subdirectory is self-contained and has its own `README.md` with
detailed instructions. The common cases:

```sh
# Assignment 02 — compile an integer constant to assembly
cd compilador-ci
python compci.py testes/p1.ci     # writes testes/p1.s

# Assignment 05 — parse and evaluate an EC1 expression
cd analise-sintatica-ec1
python ec1.py exemplos/valido3.ec1   # prints 10065

# Assignment 06 — compile an EC1 expression to x86-64 assembly
cd compilador-ec1
python compec1.py exemplos/valido3.ec1   # writes exemplos/valido3.s

# Assignment 07 — compile an EC2 expression (no mandatory parentheses)
cd compilador-ec2
python compec2.py exemplos/valido1.ec2   # "7 + 5 * 3" -> writes exemplos/valido1.s (evaluates to 22)

# Assignment 08 — compile an EV program (variable declarations + a final expression)
cd compilador-ev
python compev.py exemplos/valido2.ev     # writes exemplos/valido2.s (evaluates to 60467)

# Assignment 09 — compile a Cmd program (conditionals, loops, comparisons)
cd compilador-cmd
python compcmd.py exemplos/valido1.cmd   # writes exemplos/valido1.s (quadratic discriminant, evaluates to 8)

# Assignment 10 — compile a Fun program (functions, parameters, recursion)
cd compilador-fun
python compfun.py exemplos/valido2.fun   # writes exemplos/valido2.s (recursive fib(10), evaluates to 89)

# Run each assignment's test suite
python tests/test_parser.py               # in analise-sintatica-ec1/
python tests/test_codegen.py              # in compilador-ec1/
python tests/test_parser_precedencia.py   # in compilador-ec2/
python tests/test_ev.py                   # in compilador-ev/
python tests/test_cmd.py                  # in compilador-cmd/
python tests/test_fun.py                  # in compilador-fun/
```

To assemble and run the `.s` files produced by Assignments 02, 06, 07,
08, 09, and 10, on Linux x86-64 (use WSL on Windows):

```sh
as --64 -o out.o file.s
ld -o out out.o
./out
```

## Tech stack

- **Python** (3.8+) for the compiler implementation. No external
  dependencies; everything uses the standard library.
- **GNU Assembler (`as`)** and **`ld`** to assemble and link the generated
  output (Linux x86-64, AT&T/GAS syntax).
- **`unittest`** for the test suites.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
