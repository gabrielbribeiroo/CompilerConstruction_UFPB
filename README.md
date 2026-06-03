# CompilerConstruction_UFPB

Repository for the assignments of the **Compiler Construction 1** course,
Computer Science program at the Federal University of Paraiba (UFPB),
semester 2026.1.

- **Professor:** Andrei de Araujo Formiga
- **Term:** P6 - 2026.1

## Authors

| [<img src="https://github.com/davialves1820.png?size=100" width=100><br><sub>Davi Alves Rodrigues</sub>](https://github.com/davialves1820) | [<img src="https://github.com/gabrielbribeiroo.png?size=100" width=100><br><sub>Gabriel Ribeiro</sub>](https://github.com/gabrielbribeiroo) | [<img src="https://github.com/JoaoVitorSampaio.png?size=100" width=100><br><sub>João Vitor Sampaio</sub>](https://github.com/JoaoVitorSampaio) | [<img src="https://github.com/Nathanmn2004.png?size=100" width=100><br><sub>Nathan Meira Nobrega</sub>](https://github.com/Nathanmn2004) |
| :---: | :---: | :---: | :---: |

## Assignments

| #  | Assignment                          | Directory                                | Status    |
| -- | ----------------------------------- | ---------------------------------------- | --------- |
| 02 | CI Compiler (Integer Constants)     | [`compilador-ci/`](./compilador-ci)      | Delivered |
| 03 | Zeller's Congruence (Assembly)      | [`congruencia-zeller/`](./congruencia-zeller) | Delivered |
| 04 | Constant Expressions (Lexical Analysis) | [`expressoes-constantes/`](./expressoes-constantes) | Delivered |
| 05 | Constant Expressions (Syntactic Analysis & Interpreter) | [`analise-sintatica-ec1/`](./analise-sintatica-ec1) | Delivered |
| 06 | Constant Expressions (Full Compiler — x86-64 Codegen)   | [`compilador-ec1/`](./compilador-ec1)               | Delivered |

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
└── compilador-ec1/          # Assignment 06 - Constant Expressions 1 (Full Compiler)
    ├── lexer.py
    ├── ast_ec1.py
    ├── parser.py
    ├── codegen.py
    ├── compec1.py
    ├── runtime.s
    ├── exemplos/
    ├── tests/test_codegen.py
    ├── README.md
    ├── PLANO.md
    └── RELATORIO.md
```

## Tech stack

- **Python** for the compiler implementation.
- **GNU Assembler (`as`)** and **`ld`** to assemble and link the generated
  output (Linux x86-64, AT&T/GAS syntax).

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
