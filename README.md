# CompilerConstruction_UFPB

Repository for the assignments of the **Compiler Construction 1** course,
Computer Science program at the Federal University of Paraiba (UFPB),
semester 2026.1.

- **Professor:** Andrei de Araujo Formiga
- **Term:** P6 - 2026.1

## Team

- Davi Alves Rodrigues
- Gabriel Barbosa Ribeiro de Oliveira
- Joao Vitor Sampaio Costa
- Nathan Meira Nobrega

## Assignments

| #  | Assignment                          | Directory                                | Status    |
| -- | ----------------------------------- | ---------------------------------------- | --------- |
| 02 | CI Compiler (Integer Constants)     | [`compilador-ci/`](./compilador-ci)      | Delivered |

Each subdirectory contains the assignment's source code, a `README.md` with
usage instructions, and a `RELATORIO.md` (report) describing the work.

## Layout

```
CompilerConstruction_UFPB/
├── README.md                # this file
├── .gitignore
└── compilador-ci/           # Assignment 02 - CI Compiler
    ├── compci.py
    ├── runtime.s
    ├── README.md
    ├── RELATORIO.md
    └── testes/
        ├── p1.ci
        └── erro.ci
```

## Tech stack

- **Python 3** for the compiler implementation.
- **GNU Assembler (`as`)** and **`ld`** to assemble and link the generated
  output (Linux x86-64, AT&T/GAS syntax).
