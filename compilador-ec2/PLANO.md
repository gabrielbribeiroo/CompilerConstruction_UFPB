# Plano de Implementação — Atividade 07

**Objetivo:** estender o compilador EC1 (Atividade 06) para a linguagem
**EC2**, que permite escrever expressões com o mínimo de parênteses,
respeitando as regras usuais de **precedência** (`*`/`/` antes de `+`/`-`)
e **associatividade à esquerda** de todos os quatro operadores.

## Gramática alvo (do enunciado)

```
<exp_a> ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m> ::= <prim>  (('*' | '/') <prim>)*
<prim>  ::= <num> | '(' <exp_a> ')'
```

Essa gramática já é o resultado de duas transformações feitas no
enunciado a partir da forma ambígua/recursiva-à-esquerda original:

1. Introduzir um não-terminal por nível de precedência (`exp_a`, `exp_m`,
   `prim`) — resolve a ambiguidade de precedência.
2. Eliminar a recursão à esquerda substituindo
   `<exp> ::= <exp> '+' <termo> | <termo>` pela forma iterativa
   `<exp_a> ::= <exp_m> (('+' | '-') <exp_m>)*` — resolve o loop infinito
   que um parser descendente recursivo teria com a gramática original, e
   preserva a associatividade à esquerda (ao contrário de inverter a
   ordem para `<termo> '+' <exp>`, que dá associatividade à direita e
   quebra a subtração/divisão).

## O que muda em relação à Atividade 06

| Componente | Ação |
|---|---|
| `lexer.py` | Reusado sem alteração (já tem `proximo_token` e `olhar_proximo`). |
| `ast_ec1.py` | Reusado sem alteração — a AST (`Exp`, `Const`, `OpBin`, `Op`) não muda; só muda como ela é *construída*. |
| `codegen.py` | Reusado sem alteração — o enunciado (seção 4, "Artefato para entrega") diz explicitamente que a geração de código não muda em relação à Atividade 06. |
| `parser.py` | **Reescrito.** Troca o parser de parênteses obrigatórios da Atividade 05/06 pelo parser de precedência/associatividade descrito nas seções 2 e 3 do enunciado. |
| `compec2.py` | Novo ponto de entrada (nome do binário muda para refletir EC2), idêntico ao `compec1.py` na estrutura. |
| `runtime.s` | Reusado sem alteração. |

## Estratégia de implementação do parser

Uma função por não-terminal, seguindo o pseudocódigo do enunciado
(seção 3) ao pé da letra:

- **`_analisa_exp_a()`** — reconhece um `exp_m` (operando esquerdo),
  depois entra num laço: enquanto o próximo token (via *peek*,
  `olhar_proximo()`) for `+` ou `-`, consome o operador, reconhece outro
  `exp_m` (operando direito), e monta `OpBin(op, esq, dir)` — o nó
  recém-criado vira o novo `esq`, o que dá associatividade à esquerda
  automaticamente (a árvore cresce "para baixo e para a esquerda" a cada
  iteração, nunca aninhando à direita).
- **`_analisa_exp_m()`** — mesma estrutura que `_analisa_exp_a`, mas para
  `*`/`/` e chamando `_analisa_prim()` no lugar de `_analisa_exp_m()`.
- **`_analisa_prim()`** — se o próximo token for `NUMERO`, devolve
  `Const`; se for `PAREN_ESQ`, consome, chama `_analisa_exp_a()`
  recursivamente (aqui é onde a gramática "desce" de novo para o nível
  mais baixo de precedência dentro dos parênteses), e exige `PAREN_DIR`.
- **`analisa_programa()`** — chama `_analisa_exp_a()` e exige `EOF` em
  seguida (mesmo invariante do parser da Atividade 05, para pegar lixo
  após a expressão raiz).

O ponto crítico mencionado no enunciado — "não retirar o token do fluxo
de entrada ao verificar se é operador" — já está resolvido porque o
lexer reusado tem `olhar_proximo()` (peek) desde a Atividade 04/05.

## Testes planejados

A bateria precisa demonstrar claramente que o parser resolve precedência
e associatividade, cobrindo pelo menos:

- **Precedência**: `7 + 5 * 3` deve montar a árvore com a multiplicação
  no operando direito da soma (equivalente a `(7 + (5 * 3))`), e avaliar
  para `22`, não `36`.
- **Associatividade à esquerda em soma/subtração**: `10 - 8 - 2` deve
  significar `(10 - 8) - 2 = 0`, não `10 - (8 - 2) = 4`.
- **Associatividade à esquerda em multiplicação/divisão**: `100 / 10 / 2`
  deve significar `(100 / 10) / 2 = 5`, não `100 / (10 / 2) = 20`.
- **Parênteses ainda funcionam** e podem forçar uma ordem diferente da
  padrão: `(7 + 5) * 3` deve avaliar para `36`.
- **Mistura de tudo**: expressões com múltiplos operadores em vários
  níveis, com e sem parênteses.
- **Equivalência com o EC1**: qualquer programa EC1 válido (com
  parênteses em toda operação) deve continuar sendo aceito por EC2 e
  produzir o mesmo valor — EC2 é um superconjunto sintático de EC1.
- **Geração de código**: a AST resultante da nova análise sintática
  passa pelo mesmo `codegen.py` da Atividade 06 sem alteração —
  reaproveitamos a técnica de equivalência semântica (simulador da
  máquina de pilha comparado com `avaliar()`) já validada na atividade
  anterior.
- **Erros sintáticos**: entradas mal formadas continuam sendo detectadas
  (parêntese não fechado, token inesperado, operador sem operando).

## Estrutura dos arquivos

```
compilador-ec2/
├── lexer.py           # reusado da Atividade 04/05/06
├── ast_ec1.py         # reusado — Exp, Const, OpBin, Op
├── parser.py          # NOVO: exp_a / exp_m / prim
├── codegen.py         # reusado da Atividade 06 (sem alteração)
├── compec2.py         # novo ponto de entrada CLI
├── runtime.s          # reusado da Atividade 02/06
├── exemplos/
│   ├── valido1.ec2   # 7 + 5 * 3           -> 22
│   ├── valido2.ec2   # (7 + 5) * 3         -> 36
│   ├── valido3.ec2   # 10 - 8 - 2          -> 0
│   ├── valido4.ec2   # 100 / 10 / 2        -> 5
│   ├── valido5.ec2   # expressao mista sem parenteses
│   ├── valido6.ec2   # (33 + (912 * 11))   -> compatibilidade com EC1
│   └── invalido1.ec2 # erro sintatico proposital
├── tests/
│   └── test_parser_precedencia.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

## Itens deliberadamente fora de escopo

O enunciado (seção 3.1) discute o problema de eficiência do parser
descendente recursivo em cadeias longas de não-terminais por nível de
precedência, e menciona **escalada de precedência** (*precedence
climbing*) como a técnica que compiladores de produção usam para
resolver isso. O enunciado apresenta isso como contexto/motivação —
"por isso os compiladores... trocam para outro algoritmo" — não como
parte do que deve ser entregue nesta atividade (a seção 4, "Artefato
para entrega", pede exatamente o parser de três funções descrito na
seção 3, não escalada de precedência). Portanto, **não implementamos
escalada de precedência aqui**; o parser segue estritamente a técnica de
não-terminal-por-nível ensinada no enunciado.

## Validação

- `python tests/test_parser_precedencia.py` roda toda a suíte sem
  falhas.
- `python compec2.py exemplos/valido1.ec2` gera `.s` que, montado e
  executado, imprime `22` (não `36`).
- `python compec2.py exemplos/valido6.ec2` (um programa EC1 válido)
  continua funcionando sem alteração.
