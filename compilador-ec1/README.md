# Compilador EC1 (Atividade 06)

Compilador completo para a linguagem **EC1** (Expressões Constantes 1).
Faz análise léxica, análise sintática, constrói a árvore de sintaxe
abstrata e gera código assembly x86-64 (sintaxe GNU Assembler), produzindo
um arquivo `.s` pronto para ser montado e linkado.

Gramática:

```
<programa>        ::= <expressao>
<expressao>       ::= <literal-inteiro> | '(' <expressao> <operador> <expressao> ')'
<operador>        ::= '+' | '-' | '*' | '/'
<literal-inteiro> ::= <digito>+
```

## Requisitos

- Python 3.8 ou superior, sem dependências externas.
- Para montar e linkar o `.s` gerado: GNU Assembler (`as`) e linker (`ld`)
  em um ambiente Linux x86-64 (no Windows, use o WSL). O arquivo
  `runtime.s` (fornecido neste diretório) precisa estar visível para o `as`
  durante a montagem.

## Como usar

A partir desta pasta:

```sh
python compec1.py <arquivo.ec1>
```

O compilador grava a saída no mesmo diretório do arquivo de entrada,
trocando a extensão `.ec1` por `.s`. Por exemplo:

```sh
python compec1.py exemplos/valido3.ec1
# gera exemplos/valido3.s
```

Em caso de erro léxico ou sintático, encerra com exit code 1, mensagem em
`stderr` e nenhum `.s` é gravado.

## Montar e executar o `.s` gerado

O `.s` gerado contém `.include "runtime.s"`, então o `as` precisa
encontrá-lo no diretório de onde for invocado. A partir desta pasta:

```sh
python compec1.py exemplos/valido3.ec1
as --64 -o exemplos/valido3.o exemplos/valido3.s
ld -o exemplos/valido3 exemplos/valido3.o
./exemplos/valido3
# imprime: 10065
```

## Estrutura

```
compilador-ec1/
├── lexer.py           # Atividade 04 (reusado)
├── ast_ec1.py         # Atividade 05 (reusado)
├── parser.py          # Atividade 05 (reusado)
├── codegen.py         # gerador x86-64 (Atividade 06)
├── compec1.py         # CLI principal
├── runtime.s          # imprime_num e sair (idêntico à Atividade 02)
├── exemplos/
│   ├── valido1.ec1   # 333
│   ├── valido2.ec1   # (6 * 7)
│   ├── valido3.ec1   # (33 + (912 * 11))
│   ├── valido4.ec1   # ((427 / 7) + (11 * (231 + 5)))
│   ├── valido5.ec1   # (11 - 7)
│   └── valido6.ec1   # (7 + (3 + 8))
├── tests/test_codegen.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

## Esquema de geração (resumo)

Para cada nó da AST, o gerador emite:

| Nó | Código emitido |
|---|---|
| `Const(n)` | `mov $n, %rax` |
| `OpBin(op, esq, dir)` | código(`dir`) → `push %rax` → código(`esq`) → `pop %rbx` → instrução do operador |

Operadores:

| Op | Instrução |
|---|---|
| `SOMA` | `add %rbx, %rax` |
| `SUB`  | `sub %rbx, %rax` |
| `MULT` | `imul %rbx, %rax` |
| `DIV`  | `cqo` + `idiv %rbx` |

O esquema é o da seção 4.1 do enunciado, opção 2 (ordem invertida):
emite o operando direito primeiro, empilha, depois o esquerdo. Após o
`pop %rbx`, `%rax` tem o operando esquerdo e `%rbx` o direito — ordem
natural para `sub` e `idiv`.

## Testes

```sh
python tests/test_codegen.py
```

Inclui 15 testes em 6 classes:

- **`TestCodigoDeConstantes`** — `Const(n)` → `mov $n, %rax`.
- **`TestCodigoDeOperacoes`** — código literal exato para cada operador.
- **`TestAninhamento`** — pilha balanceada em expressões aninhadas.
- **`TestEquivalenciaSemantica`** — simula em Python a máquina de pilha
  do código gerado e compara com o `avaliar()` do interpretador
  (Atividade 05) para 16 programas, incluindo os dois exemplos do
  enunciado e casos não-comutativos aninhados.
- **`TestProgramaCompleto`** — verifica que `gerar_programa()` envolve o
  código no modelo `.s` correto (seção, `_start`, chamadas finais,
  `.include`).
- **`TestCLI`** — invoca `compec1.py` como subprocesso e verifica que o
  arquivo `.s` é gravado para entrada válida e que entrada inválida
  resulta em exit 1 e nenhum `.s` produzido.

## Exemplos fornecidos

| Arquivo | Conteúdo | Resultado ao executar |
|---|---|---|
| `valido1.ec1` | `333` | `333` |
| `valido2.ec1` | `(6 * 7)` | `42` |
| `valido3.ec1` | `(33 + (912 * 11))` | `10065` |
| `valido4.ec1` | `((427 / 7) + (11 * (231 + 5)))` | `2657` |
| `valido5.ec1` | `(11 - 7)` | `4` |
| `valido6.ec1` | `(7 + (3 + 8))` | `18` |
