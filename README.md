# CompilerConstruction_UFPB

Repository for the assignments of the **Compiler Construction 1** course,
Computer Science program at the Federal University of Paraíba (UFPB),
semester 2026.1.

- **Professor:** Andrei de Araújo Formiga
- **Term:** P6 - 2026.1

Across assignments 02 through 08 we build a small compiler step by step,
finishing with complete compilers for the **EC1**/**EC2**/**EV** languages
(Constant Expressions 1/2, Expressions with Variables): a lexer (04), a
recursive-descent parser plus tree-walking interpreter (05), an x86-64
code generator (06) that ties everything together, a
precedence/associativity-aware parser (07) that lets expressions be
written without mandatory parentheses, and variable declarations plus a
semantic-analysis pass with a symbol table (08). Assignment 02 was a
warm-up compiler for integer constants, and Assignment 03 was a
hand-written assembly exercise (Zeller's Congruence) that informed the
codegen scheme used in Assignment 06.

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
└── compilador-ev/           # Assignment 08 - Expressions with Variables
    ├── lexer.py             # extended: IDENT, IGUAL, PONTO_VIRGULA
    ├── ast_ev.py            # Exp, Const, OpBin, Op, Var, Decl, Programa
    ├── parser.py            # programa / decl / exp / exp_m / prim
    ├── semantica.py         # NEW: symbol table + variable-use checking
    ├── codegen.py           # extended: .bss section, load/store variables
    ├── compev.py
    ├── runtime.s            # identical to Assignment 06
    ├── exemplos/
    ├── tests/test_ev.py
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

# Run each assignment's test suite
python tests/test_parser.py               # in analise-sintatica-ec1/
python tests/test_codegen.py              # in compilador-ec1/
python tests/test_parser_precedencia.py   # in compilador-ec2/
python tests/test_ev.py                   # in compilador-ev/
```

To assemble and run the `.s` files produced by Assignments 02, 06, 07,
and 08, on Linux x86-64 (use WSL on Windows):

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
