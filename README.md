# CompilerConstruction_UFPB

Repositorio das atividades da disciplina **Construcao de Compiladores 1**,
do curso de Ciencia da Computacao da Universidade Federal da Paraiba (UFPB),
semestre 2026.1.

- **Professor:** Andrei de Araujo Formiga
- **Periodo:** P6 - 2026.1

## Integrantes do grupo

| Nome                                       | Matricula     |
| ------------------------------------------ | ------------- |
| Davi Alves Rodrigues                       | 20230102377   |
| Gabriel Barbosa Ribeiro de Oliveira        | 20230012814   |
| Joao Vitor Sampaio Costa                   | 20230089776   |
| Nathan Meira Nobrega                       | 20240008904   |

## Atividades

| # | Atividade                                  | Diretorio                                       | Status     |
| - | ------------------------------------------ | ----------------------------------------------- | ---------- |
| 02 | Compilador CI (Constantes Inteiras)       | [`compilador-ci/`](./compilador-ci)             | Entregue   |

Cada subdiretorio contem o codigo-fonte da atividade, um `README.md` com
instrucoes de execucao e um `RELATORIO.md` com a descricao do trabalho.

## Estrutura

```
CompilerConstruction_UFPB/
├── README.md                # este arquivo
├── .gitignore
└── compilador-ci/           # Atividade 02 - Compilador CI
    ├── compci.py
    ├── runtime.s
    ├── README.md
    ├── RELATORIO.md
    └── testes/
        ├── p1.ci
        └── erro.ci
```

## Tecnologias

- **Python 3** para a implementacao do compilador.
- **GNU Assembler (`as`)** e **`ld`** para montar e linkar o assembly gerado
  (Linux x86-64, sintaxe AT&T/GAS).
