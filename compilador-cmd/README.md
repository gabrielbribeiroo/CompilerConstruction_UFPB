# Compilador Cmd (Atividade 09)

Compilador completo para a linguagem **Cmd**, que estende EV
(Atividade 08) com **comandos** — condicional (`if`/`else`), repetição
(`while`) e atribuição — e **operadores de comparação** (`<`, `>`,
`==`). É a primeira linguagem deste conjunto de compiladores que é
**Turing-completa**.

Um programa Cmd é zero ou mais declarações, seguidas de um corpo entre
chaves com zero ou mais comandos e uma expressão final obrigatória
(`return exp;`). Não há tipo booleano separado: zero é falso, qualquer
outro valor é verdadeiro.

Exemplo (valor absoluto do discriminante de uma equação de 2º grau):

```
a = 1;
b = 2;
c = 3;
delta = b * b - 4 * a * c;
{
  if delta < 0 {
    delta = 0 - delta;
  } else {
    delta = delta;
  }
  return delta;
}
```

Gramática:

```
<programa> ::= <decl>* '{' <cmd>* 'return' <exp> ';' '}'
<decl>     ::= <var> '=' <exp> ';'
<cmd>      ::= <if> | <while> | <atrib>
<if>       ::= 'if' <exp> '{' <cmd>* '}' 'else' '{' <cmd>* '}'
<while>    ::= 'while' <exp> '{' <cmd>* '}'
<atrib>    ::= <var> '=' <exp> ';'
<exp>      ::= <exp_a> (('<' | '>' | '==') <exp_a>)*
<exp_a>    ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m>    ::= <prim> (('*' | '/') <prim>)*
<prim>     ::= <num> | <var> | '(' <exp> ')'
```

O braço `else` é **obrigatório** (pode ser um bloco vazio `{ }`).
`return` não é um comando — só aparece uma vez, no fim do programa.
A atribuição não cria variáveis novas: só é permitida para variáveis
já declaradas antes do corpo de comandos.

## Requisitos

- Python 3.8 ou superior, sem dependências externas.
- Para montar e linkar o `.s` gerado: GNU Assembler (`as`) e linker
  (`ld`) em um ambiente Linux x86-64 (no Windows, use o WSL). O
  `runtime.s` (fornecido neste diretório) precisa estar visível para o
  `as` durante a montagem.

## Como usar

A partir desta pasta:

```sh
python compcmd.py <arquivo.cmd>
```

O compilador grava a saída no mesmo diretório da entrada, trocando a
extensão `.cmd` por `.s`. Exemplo:

```sh
python compcmd.py exemplos/valido1.cmd
# gera exemplos/valido1.s
```

Em caso de erro léxico, sintático ou semântico (uso ou atribuição de
variável não declarada), encerra com exit code 1, mensagem em `stderr`
e nenhum `.s` é gravado.

## Montar e executar o `.s` gerado

```sh
python compcmd.py exemplos/valido1.cmd
as --64 -o exemplos/valido1.o exemplos/valido1.s
ld -o exemplos/valido1 exemplos/valido1.o
./exemplos/valido1
# imprime: 8   (valor absoluto do discriminante)
```

## Estrutura

```
compilador-cmd/
├── lexer.py           # estendido: {, }, <, >, ==, if/else/while/return
├── ast_cmd.py         # Exp/Const/Var/OpBin/Op + Atrib/If/While/Programa
├── parser.py          # programa / cmd / if / while / atrib / exp (comparação) / exp_a / exp_m / prim
├── semantica.py         # TabelaSimbolos + verifica_programa (recursivo em cmds)
├── codegen.py         # comparações (cmp+setz/setl/setg) + if/while com rótulos
├── compcmd.py         # CLI: lex -> parse -> semântica -> codegen
├── runtime.s          # reusado sem alteração (Atividade 02/06/07/08)
├── exemplos/
│   ├── valido1.cmd    # discriminante (enunciado)             -> 8
│   ├── valido2.cmd    # soma de n a m-1 via while (enunciado)  -> 45
│   ├── valido3.cmd    # resto da divisão (seção 9)             -> 2
│   ├── valido4.cmd    # mdc (seção 9)                          -> 6
│   ├── invalido_atrib_var_nao_declarada.cmd
│   └── invalido_atrib_direita_nao_declarada.cmd
├── tests/test_cmd.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

## O que muda em relação à Atividade 08

Igual à Atividade 08 (e diferente da 07), **todos os estágios**
mudaram:

| Estágio | Mudança |
|---|---|
| Léxico | Tokens novos: `{`, `}`, `<`, `>`, `==`, e as palavras-chave `if`/`else`/`while`/`return` |
| Sintático | Novo nível de precedência `exp` (comparação), abaixo de `exp_a`; comandos (`if`/`while`/atribuição) |
| Semântico | Verificação de atribuição: lado direito (expressão) e lado esquerdo (variável) precisam já estar declarados; percorre `if`/`while` recursivamente |
| Codegen | Comparações via `cmp`+`setz`/`setl`/`setg`; `if`/`while` via `cmp $0, %rax` + `jz` + rótulos com contador incremental |

## Testes

```sh
python tests/test_cmd.py
```

35 testes em 7 classes: léxico (tokens novos, `==` vs `=`, palavras-chave
vs. identificadores), parser (estrutura da AST para `if`/`while`/atribuição),
erros sintáticos, análise semântica (atribuição a variável não declarada
nos dois lados, inclusive dentro de blocos aninhados), interpretação
(os 4 exemplos do enunciado — discriminante, soma, resto, mdc),
equivalência semântica entre o código gerado e o interpretador (um
simulador de máquina de pilha **com rótulos e desvios** — `jmp`/`jz` —
além de memória e comparações), e o comportamento do CLI via subprocess.

## Exemplos fornecidos

| Arquivo | Conteúdo | Resultado |
|---|---|---|
| `valido1.cmd` | Discriminante de `x² + 2x + 3` (valor absoluto) | `8` |
| `valido2.cmd` | Soma de `n` a `m-1` (`n=1, m=10`) via `while` | `45` |
| `valido3.cmd` | Resto de `10 / 4` por subtração sucessiva | `2` |
| `valido4.cmd` | MDC de `18` e `12` | `6` |
| `invalido_atrib_var_nao_declarada.cmd` | Atribuição a variável nunca declarada | erro semântico (`y`), exit 1 |
| `invalido_atrib_direita_nao_declarada.cmd` | Expressão de atribuição referencia variável não declarada | erro semântico (`w`), exit 1 |

## Variação sintática

Seguimos exatamente a sintaxe do enunciado, sem adotar nenhuma das
extensões citadas na seção 7 (operadores `<=`/`>=`, operadores
booleanos, comando de entrada, `if` sem `else`, atribuição que cria
variáveis) — todas apresentadas como opcionais.
