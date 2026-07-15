# Plano de Implementação — Atividade 09

**Objetivo:** estender o compilador EV (Atividade 08) para a linguagem
**Cmd**, adicionando comandos (`if`/`else`, `while`, atribuição) e
operadores de comparação (`<`, `>`, `==`). Com isso o compilador passa
a gerar programas para nossa primeira linguagem **Turing-completa**.

## Gramática alvo (do enunciado)

```
<programa> ::= <decl>* '{' <cmd>* 'return' <exp> ';' '}'
<decl>     ::= <var> '=' <exp> ';'
<var>      ::= <letra><letra_digito>*
<cmd>      ::= <if> | <while> | <atrib>
<if>       ::= 'if' <exp> '{' <cmd>* '}' 'else' '{' <cmd>* '}'
<while>    ::= 'while' <exp> '{' <cmd>* '}'
<atrib>    ::= <var> '=' <exp> ';'
<exp>      ::= <exp_a> (('<' | '>' | '==') <exp_a>)*
<exp_a>    ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m>    ::= <prim> (('*' | '/') <prim>)*
<prim>     ::= <num> | <var> | '(' <exp> ')'
```

Um programa é zero ou mais declarações, seguidas de um corpo entre
chaves com zero ou mais comandos e uma expressão final obrigatória
(`return exp;`). `return` não é um comando — só pode aparecer uma vez,
no fim do corpo do programa (não dentro de `if`/`while`).

## O que muda em relação à Atividade 08 (EV)

Igual à Atividade 08, e diferente da 07 (onde tudo era herdado sem
alteração), aqui **todos os estágios** mudam:

| Componente | Ação |
|---|---|
| `lexer.py` | **Estendido**: `{`, `}`, `<`, `>`, `==`, e as palavras-chave `if`, `else`, `while`, `return`. `==` exige lookahead de 1 caractere para diferenciar de `=`. Palavras-chave são reconhecidas como identificadores e só então comparadas contra uma tabela fixa. |
| `ast_cmd.py` | **Estendido**: `Exp`/`Const`/`Var`/`OpBin`/`Op` reaproveitados, `Op` ganha `MENOR`/`MAIOR`/`IGUAL`. Novos nós de comando: `Atrib`, `If`, `While`. `Programa` ganha `comandos: tuple[Cmd, ...]` além de `declaracoes` e `exp_final`. |
| `parser.py` | **Estendido**: novo nível de precedência `exp` (comparação, abaixo de `exp_a`); `_analisa_cmd()` despacha por *peek* entre `if`/`while`/identificador (atribuição). |
| `semantica.py` | **Estendido**: `_verifica_cmd()` percorre recursivamente `If`/`While` (incluindo os dois braços do `if`); `Atrib` verifica a expressão do lado direito E que a variável do lado esquerdo já foi declarada — sem inserir nada na tabela (atribuição não cria variáveis). |
| `codegen.py` | **Estendido**: operadores de comparação via `cmp`+`setz`/`setl`/`setg`; `if`/`while` via `cmp $0, %rax` + `jz` + rótulos com contador incremental. |
| `compcmd.py` | Novo ponto de entrada, mesma estrutura das atividades anteriores. |
| `runtime.s` | Reusado sem alteração. |

## Análise léxica

Tokens novos: `CHAVE_ESQ` (`{`), `CHAVE_DIR` (`}`), `MENOR` (`<`),
`MAIOR` (`>`), `IGUAL_IGUAL` (`==`), e as palavras-chave `PALAVRA_IF`,
`PALAVRA_ELSE`, `PALAVRA_WHILE`, `PALAVRA_RETURN`.

- **`==` vs `=`**: ao encontrar `=`, o lexer olha o próximo caractere
  (sem consumi-lo até decidir); se for outro `=`, o token é
  `IGUAL_IGUAL` (consome os dois caracteres); senão, é `IGUAL`
  (consome só um).
- **Palavras-chave**: reconhecidas com a mesma regra léxica de
  identificador (`letra letra_digito*`); só depois de montar o lexema
  completo é que se compara contra uma tabela fixa
  (`if`/`else`/`while`/`return`) para decidir o tipo do token — a
  técnica sugerida na seção 3 do enunciado.

## Árvore de sintaxe abstrata

Reaproveitamos `Exp`/`Const`/`Var`/`OpBin` das atividades anteriores.
`Op` ganha três valores para os operadores de comparação:
`MENOR` (`<`), `MAIOR` (`>`), `IGUAL` (`==`). Não existe tipo booleano
separado — o resultado de uma comparação é sempre `0` ou `1`.

Novos nós, todos usando a mesma convenção de `dataclass(frozen=True)`:

- **`Atrib(nome, exp, posicao)`** — comando de atribuição. `posicao`
  (não comparável) guarda a posição do identificador para mensagens de
  erro semântico, como `Var.posicao` na Atividade 08.
- **`If(cond, cmds_then, cmds_else)`** — o braço `else` é obrigatório
  na gramática (mas pode ser um bloco vazio).
- **`While(cond, cmds)`**.
- **`Programa(declaracoes, comandos, exp_final)`** — ganhou o campo
  `comandos`.

`Programa.avaliar()` continua sendo o interpretador de referência,
usado para validar a geração de código: processa as declarações,
depois executa os comandos sequencialmente (com um interpretador
recursivo simples que resolve `If`/`While` chamando a si mesmo para os
sub-blocos), e por fim avalia a expressão final.

## Análise sintática

`_analisa_cmd()` decide por *peek* de 1 token, exatamente como o
enunciado descreve: `if` → comando condicional, `while` → repetição,
identificador → atribuição. A lista de comandos dentro de qualquer
bloco (`programa`, braços do `if`, corpo do `while`) termina quando o
próximo token não é mais um desses três indicadores.

A gramática ganha um nível de precedência novo, `exp` (comparação),
**abaixo** de `exp_a` (aditivo) — os operadores de comparação têm a
precedência mais baixa da linguagem. A função `_analisa_exp()` segue
exatamente o mesmo formato de laço já usado em `_analisa_exp_a()` e
`_analisa_exp_m()`, apenas trocando o conjunto de operadores e a
função de nível inferior chamada (`_analisa_exp_a()`).

## Análise semântica

Estende `verifica_programa()` da Atividade 08 com `_verifica_cmd()`,
que percorre recursivamente comandos `If`/`While` (checando a condição
e os comandos dos blocos). Para `Atrib`, a ordem de verificação segue a
ordem natural de execução: primeiro a expressão do lado direito
(precisa estar totalmente declarada), depois a variável do lado
esquerdo (precisa já existir). Como a atribuição não cria variáveis
novas, nada é adicionado à tabela de símbolos ao processar um `Atrib`
— só as declarações (`Decl`) inserem símbolos, exatamente como o
enunciado explicita na seção 5.

## Geração de código

### Comparações (seção 6.1 do enunciado)

Reaproveitamos o esquema de pilha já usado para `OpBin` aritmético
(`dir` primeiro, `push`, `esq`, `pop %rbx` → `%rax = esq`,
`%rbx = dir`). Para uma comparação, em vez de `add`/`sub`/`imul`,
emitimos:

```
xor %rcx, %rcx
cmp %rbx, %rax
set<cc> %cl
mov %rcx, %rax
```

onde `set<cc>` é `setz` (`==`), `setl` (`<`) ou `setg` (`>`). O
resultado (0 ou 1) fica em `%rax`, seguindo a convenção da linguagem de
que zero é falso e qualquer outro valor é verdadeiro.

### `if`/`else` e `while` (seção 6.2 do enunciado)

Cada `if` e `while` gerado usa um contador interno de rótulos
(`GeradorDeCodigo._proximo_rotulo()`) para produzir nomes únicos
(`Lfalso0`, `Lfim0`, `Linicio1`, `Lfim1`, ...). Os modelos de tradução
seguem exatamente o enunciado:

```
# if E { C1 } else { C2 }
<codigo_E>
cmp $0, %rax
jz LfalsoN
<codigo_C1>
jmp LfimN
LfalsoN:
<codigo_C2>
LfimN:
```

```
# while E { C }
LinicioN:
<codigo_E>
cmp $0, %rax
jz LfimN
<codigo_C>
jmp LinicioN
LfimN:
```

### Modelo de saída

Mesmo modelo com seções `.bss`/`.text` da Atividade 08 — as variáveis
declaradas continuam gerando `.lcomm`, e o corpo agora inclui os
comandos (com `if`/`while`/`jmp`/rótulos) antes do código da expressão
final.

## Variação sintática

Seguimos exatamente a sintaxe proposta no enunciado (seção 2 e 2.1),
sem adotar nenhuma das variações citadas na seção 7 (operadores `<=`/
`>=`, operadores booleanos, comando de entrada, `if` sem `else`,
atribuição criando variáveis) — todas apresentadas como extensões
opcionais.

## Estrutura dos arquivos

```
compilador-cmd/
├── lexer.py           # estendido: chaves, <, >, ==, palavras-chave
├── ast_cmd.py         # Exp/Const/Var/OpBin/Op + Atrib/If/While/Programa
├── parser.py          # programa / cmd / if / while / atrib / exp (comparação) / exp_a / exp_m / prim
├── semantica.py        # TabelaSimbolos + verifica_programa (recursivo em cmds)
├── codegen.py         # comparacoes + if/while com rotulos
├── compcmd.py         # CLI: lex -> parse -> semantica -> codegen
├── runtime.s          # reusado sem alteracao
├── exemplos/
│   ├── valido1.cmd    # discriminante (do enunciado)          -> 8
│   ├── valido2.cmd    # soma de n a m-1 via while (enunciado)  -> 45
│   ├── valido3.cmd    # resto da divisao (secao 9)             -> 2
│   ├── valido4.cmd    # mdc (secao 9)                          -> 6
│   ├── invalido_atrib_var_nao_declarada.cmd
│   └── invalido_atrib_direita_nao_declarada.cmd
├── tests/
│   └── test_cmd.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

## Testes planejados

- **Léxico**: `{`, `}`, `<`, `>`, `==` vs `=`, palavras-chave
  reconhecidas corretamente (não confundidas com identificadores de
  mesmo prefixo, ex.: `ifx` é identificador, não `if`).
- **Sintático**: estrutura da AST para programas com `if`/`else` e
  `while`; erro sintático para `if` sem `else`, bloco sem chaves, etc.
- **Semântico**: atribuição a variável não declarada (lado esquerdo e
  lado direito, em casos separados), inclusive dentro de `if`/`while`
  aninhados; programas válidos passam sem erro.
- **Interpretação** (`Programa.avaliar()`): os quatro exemplos do
  enunciado (discriminante, soma, resto, mdc) devem avaliar para os
  valores citados (8, 45, 2, 6).
- **Geração de código / equivalência semântica**: um simulador de
  máquina de pilha estendido com **rótulos e desvios** (`jmp`, `jz`)
  além de memória (variáveis) e comparações (`cmp`, `setz`/`setl`/
  `setg`), comparado com `avaliar()` do interpretador para os mesmos
  programas — prova que o código gerado (incluindo laços) é
  semanticamente equivalente ao interpretador, sem precisar montar e
  rodar o `.s` de fato.
- **CLI**: `compcmd.py` grava `.s` para entrada válida; erro léxico,
  sintático ou semântico produz exit 1 sem gravar `.s`.

## Itens deliberadamente fora de escopo

Nenhuma das extensões da seção 7 do enunciado foi implementada:
`<=`/`>=`, operadores booleanos (`AND`/`OR`/`NOT`), comando de entrada,
`if` sem `else`, ou atribuição que cria variáveis novas. Todas são
citadas explicitamente como possibilidades opcionais, não como parte
do artefato mínimo pedido na seção 8.

## Validação

- `python tests/test_cmd.py` roda toda a suíte sem falhas.
- `python compcmd.py exemplos/valido1.cmd` gera `.s` que, montado e
  executado, imprime `8` (discriminante absoluto).
- `python compcmd.py exemplos/invalido_atrib_var_nao_declarada.cmd`
  encerra com exit 1 e mensagem clara no `stderr`, sem gerar `.s`.
