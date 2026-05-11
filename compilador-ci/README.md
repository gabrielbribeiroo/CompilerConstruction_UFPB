# Compilador CI (Constantes Inteiras)

Compilador para a linguagem CI definida na Atividade 02 da disciplina
Construcao de Compiladores 1. Um programa em CI e apenas uma constante
inteira; o compilador gera um arquivo assembly x86-64 (sintaxe GNU Assembler)
que imprime essa constante na tela.

## Requisitos

- Python 3.8 ou superior (nenhuma dependencia externa).
- Para gerar o executavel final a partir do `.s`: GNU Assembler (`as`) e linker
  (`ld`), em um ambiente Linux x86-64 (no Windows, basta usar WSL).

O arquivo `runtime.s`, incluido na raiz do projeto, contem os procedimentos
`imprime_num` e `sair` chamados pelo modelo de saida e precisa estar visivel
para o `as` no momento da montagem (veja a secao "Como montar e linkar").

## Estrutura

```
compilador-ci/
├── compci.py        # o compilador
├── runtime.s        # rotinas de runtime (imprime_num, sair)
├── README.md
├── RELATORIO.md
└── testes/
    ├── p1.ci        # entrada valida: 42
    └── erro.ci      # entrada invalida: 42abc
```

## Como compilar o compilador

Nao precisa. O compilador esta escrito em Python e e executado diretamente.

## Como executar o compilador

A partir da raiz do projeto:

```sh
python3 compci.py <arquivo.ci>
```

O compilador grava o arquivo de saida com o mesmo nome do arquivo de entrada,
trocando a extensao `.ci` por `.s`. Por exemplo:

```sh
python3 compci.py testes/p1.ci
# gera testes/p1.s
```

## Como montar e linkar (gerar o executavel)

O `.s` gerado contem `.include "runtime.s"`, e o `as` procura esse include
**no diretorio de onde o comando e executado**. Portanto, execute o `as` a
partir da raiz do projeto (onde esta o `runtime.s`):

```sh
# a partir da raiz do projeto
python3 compci.py testes/p1.ci
as --64 -o testes/p1.o testes/p1.s
ld -o testes/p1 testes/p1.o
./testes/p1
# saida esperada: 42
```

Se preferir rodar o `as` de dentro de `testes/`, copie o `runtime.s` para la
antes:

```sh
cp runtime.s testes/
cd testes
as --64 -o p1.o p1.s
ld -o p1 p1.o
./p1
```

## Testes inclusos

- `testes/p1.ci` — programa correto (`42`). O compilador gera `testes/p1.s`
  e, apos montar e linkar, o executavel imprime `42` na tela.
- `testes/erro.ci` — programa com erro de sintaxe (`42abc`). O compilador
  encerra com mensagem no `stderr` e codigo de saida 1, sem gerar `.s`.

Para rodar os dois testes:

```sh
python3 compci.py testes/p1.ci
python3 compci.py testes/erro.ci
```
