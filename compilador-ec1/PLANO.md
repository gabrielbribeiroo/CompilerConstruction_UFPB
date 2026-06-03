# Plano de Implementação — Atividade 06

**Objetivo:** completar o compilador EC1 adicionando geração de código x86-64.
O compilador integra lexer (Atividade 04), parser (Atividade 05) e o novo
gerador de código (Atividade 06), produzindo um arquivo `.s` pronto para ser
montado e linkado, seguindo o modelo de saída da Atividade 02.

## Esquema de geração

Esquema de tradução baseado na pilha (seção 4 do enunciado), usando a
**ordem invertida dos operandos** (opção 2 da seção 4.1, página 9), porque
ela coloca naturalmente `esq` em `%rax` e `dir` em `%rbx` antes da operação,
o que resolve a ordem correta para operadores não-comutativos (`sub`, `idiv`)
sem nenhum truque extra.

Regras de tradução:

- **`Const(n)`** → `mov $n, %rax`
- **`OpBin(op, esq, dir)`**:
  1. Gera código de `dir` (resultado em `%rax`)
  2. `push %rax`
  3. Gera código de `esq` (resultado em `%rax`)
  4. `pop %rbx` (operando direito agora em `%rbx`)
  5. Emite instrução da operação:
     - `SOMA` → `add %rbx, %rax`
     - `SUB`  → `sub %rbx, %rax`
     - `MULT` → `imul %rbx, %rax`
     - `DIV`  → `cqo` + `idiv %rbx` (sign-extend e divisão inteira com sinal;
       quociente fica em `%rax`)

Esse esquema preserva o invariante da pilha: para qualquer subexpressão, ela
empilha e desempilha exatamente um valor, deixando o `%rsp` no mesmo estado
ao terminar.

## Modelo de saída

O `.s` final segue o modelo do enunciado (seção 5), idêntico ao da
Atividade 02:

```
    .section .text
    .globl _start
_start:
    <codigo da expressao>
    call imprime_num
    call sair

    .include "runtime.s"
```

## Estrutura

```
compilador-ec1/
├── lexer.py           # Atividade 04
├── ast_ec1.py         # Atividade 05
├── parser.py          # Atividade 05
├── codegen.py         # NOVO: gerador x86-64
├── compec1.py         # NOVO: CLI principal (lê .ec1, escreve .s)
├── runtime.s          # mesmo arquivo da Atividade 02
├── exemplos/
│   ├── valido1.ec1   # 333
│   ├── valido2.ec1   # (6 * 7)
│   ├── valido3.ec1   # (33 + (912 * 11))
│   ├── valido4.ec1   # ((427 / 7) + (11 * (231 + 5)))
│   ├── valido5.ec1   # (11 - 7)   — testa não-comutatividade
│   └── valido6.ec1   # (7 + (3 + 8))
├── tests/
│   └── test_codegen.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

## Testes planejados

A bateria deve cobrir:

- **Tradução de constantes**: `Const(n)` produz `mov $n, %rax`.
- **Operações comutativas e não-comutativas**: cada um dos quatro
  operadores em isolamento.
- **Aninhamento**: a tradução de `(7 + (3 + 8))` precisa produzir uma
  sequência push/pop balanceada e usar a pilha duas vezes.
- **Os dois exemplos do enunciado** (`(33 + (912 * 11))` e
  `((427 / 7) + (11 * (231 + 5)))`).
- **Programa completo**: o `.s` gerado pelo `compec1.py` precisa ter o
  cabeçalho do modelo, o código da expressão e as chamadas finais
  `call imprime_num` e `call sair`.
- **Equivalência semântica**: para cada AST de teste, executar o esquema
  na pilha simulado em Python e comparar com o `avaliar()` do interpretador
  da Atividade 05. Se os dois produzem o mesmo valor, o codegen é
  semanticamente correto (mesmo sem montar e rodar o `.s`).
- **CLI**: invocar `compec1.py arquivo.ec1` gera `arquivo.s` ao lado e o
  conteúdo bate com o gerado pela API.
- **Programas inválidos**: `compec1.py` deve falhar com exit 1 e sem
  produzir `.s` para entrada com erro sintático ou léxico.

## Itens deliberadamente NÃO implementados

A seção 7 do enunciado discute otimização (alocação de registradores mais
inteligente para usar menos pilha; propagação de constantes para reduzir
toda a expressão a um único `mov`). Essas otimizações são apresentadas
como *o que ficou de fora*, não como o que se pede para entregar — não
serão implementadas. O esquema com pilha simples é exatamente o que a
seção 4 descreve e é o que entregamos.

## Validação

- `python compec1.py exemplos/valido1.ec1` gera `exemplos/valido1.s` com o
  modelo completo + a única instrução `mov $333, %rax`.
- `python compec1.py exemplos/valido3.ec1` gera `exemplos/valido3.s` que,
  ao ser montado/linkado (no Linux x86-64 com `runtime.s` no mesmo
  diretório) e executado, imprime `10065`.
- `python tests/test_codegen.py` roda toda a suíte sem falhas.
