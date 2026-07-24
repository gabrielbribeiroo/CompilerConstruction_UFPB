# Compilador Fun (Atividade 10)

Compilador completo para a linguagem **Fun**, que estende Cmd
(Atividade 09) com **declaração de funções** — com parâmetros,
variáveis locais e recursão (direta) — usando uma convenção de
chamada baseada em pilha, com `%rbp` como *frame pointer*.

Um programa Fun é zero ou mais declarações (de variável global ou de
função), seguidas de um bloco `main` com zero ou mais comandos e uma
expressão final obrigatória (`return exp;`).

Exemplo (valor absoluto, do enunciado):

```
fun abs(x) {
  var y = 0;
  if x < 0 {
    y = 0 - x;
  } else {
    y = x;
  }
  return y;
}

main {
  return abs(0 - 42);
}
```

Gramática:

```
<programa>  ::= <decl>* 'main' '{' <cmd>* 'return' <exp> ';' '}'
<decl>      ::= <vardecl> | <fundecl>
<vardecl>   ::= 'var' <ident> '=' <exp> ';'
<fundecl>   ::= 'fun' <ident> '(' <params>? ')' '{' <vardecl>* <cmd>* 'return' <exp> ';' '}'
<params>    ::= <ident> (',' <ident>)*
<cmd>       ::= <if> | <while> | <atrib>
<if>        ::= 'if' <exp> '{' <cmd>* '}' 'else' '{' <cmd>* '}'
<while>     ::= 'while' <exp> '{' <cmd>* '}'
<atrib>     ::= <ident> '=' <exp> ';'
<exp>       ::= <exp_a> (('<' | '>' | '==') <exp_a>)*
<exp_a>     ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m>     ::= <prim> (('*' | '/') <prim>)*
<prim>      ::= <num> | <chamada> | <ident> | '(' <exp> ')'
<chamada>   ::= <ident> '(' <args>? ')'
<args>      ::= <exp> (',' <exp>)*
```

Variáveis locais de uma função (`var` dentro do corpo da função,
antes dos comandos) escondem variáveis globais de mesmo nome dentro
daquela função. Uma função pode chamar a si mesma (recursão direta),
mas **não** pode chamar outra função declarada depois dela no texto
(recursão mútua é opcional/fora de escopo — ver seção abaixo).

## Requisitos

- Python 3.8 ou superior, sem dependências externas.
- Para montar e linkar o `.s` gerado: GNU Assembler (`as`) e linker
  (`ld`) em um ambiente Linux x86-64 (no Windows, use o WSL). O
  `runtime.s` (fornecido neste diretório) precisa estar visível para o
  `as` durante a montagem.

## Como usar

A partir desta pasta:

```sh
python compfun.py <arquivo.fun>
```

O compilador grava a saída no mesmo diretório da entrada, trocando a
extensão `.fun` por `.s`. Exemplo:

```sh
python compfun.py exemplos/valido2.fun
# gera exemplos/valido2.s
```

Em caso de erro léxico, sintático ou semântico (função/variável não
declarada, número de parâmetros incorreto, etc.), encerra com exit
code 1, mensagem em `stderr` e nenhum `.s` é gravado.

## Montar e executar o `.s` gerado

```sh
python compfun.py exemplos/valido2.fun
as --64 -o exemplos/valido2.o exemplos/valido2.s
ld -o exemplos/valido2 exemplos/valido2.o
./exemplos/valido2
# imprime: 89   (fib(10), com fib(0) = fib(1) = 1)
```

## Estrutura

```
compilador-fun/
├── lexer.py           # estendido: vírgula, fun/var/main
├── ast_fun.py         # Exp/Const/Var/OpBin/Chamada + Cmd/Atrib/If/While
│                      # + VarDecl/FunDecl/Programa (com avaliar() para cada um)
├── parser.py          # decl (vardecl|fundecl) / parametros / argumentos / chamada vs. var
├── semantica.py       # TabelaSimbolos (globais + funcoes) + escopo local por funcao
├── codegen.py         # convencao de chamada: push/call/cleanup, prologo/epilogo com %rbp
├── compfun.py         # CLI: lex -> parse -> semantica -> codegen
├── runtime.s          # reusado sem alteracao (Atividade 02/06/07/08/09)
├── exemplos/
│   ├── valido1.fun    # abs() (exemplo do enunciado)                    -> 42
│   ├── valido2.fun    # fib() recursiva (exemplo do enunciado)          -> 89
│   ├── valido3.fun    # funcao chamando outra funcao                    -> 25
│   ├── valido4.fun    # variavel local esconde global de mesmo nome     -> 110
│   ├── invalido_funcao_nao_declarada.fun
│   ├── invalido_numero_de_parametros.fun
│   └── invalido_variavel_fora_de_escopo.fun
├── tests/test_fun.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

## O que muda em relação à Atividade 09

Como na Atividade 09 (e nas anteriores), **todos os estágios**
mudaram:

| Estágio | Mudança |
|---|---|
| Léxico | Token novo: `,`; palavras-chave `fun`/`var`/`main` |
| Sintático | `VarDecl`/`FunDecl` no nível de programa; lista de parâmetros formais; chamada de função (`Chamada`) desambiguada de `Var` por um token de *lookahead* (`(` depois do identificador) |
| Semântico | Tabela de símbolos com dois espaços de nomes (variáveis e funções); escopo léxico (local antes de global); recursão direta permitida registrando a função antes de verificar seu próprio corpo |
| Codegen | Convenção de chamada com pilha: argumentos empilhados em ordem inversa antes do `call`, limpeza pelo chamador depois; prólogo/epílogo de função com `%rbp` como *frame pointer*; acesso a variável local/parâmetro via deslocamento de `%rbp` |

## Testes

```sh
python tests/test_fun.py
```

40 testes em 8 classes: léxico (token de vírgula, palavras-chave
novas), parser (`FunDecl` com zero/um/vários parâmetros, `Chamada`
distinguida de `Var`, lista de argumentos), erros sintáticos, análise
semântica (função/variável não declarada, número de parâmetros
incorreto, escopo de variável local, recursão direta permitida,
recursão *mútua* corretamente rejeitada), interpretação
(`Programa.avaliar()` para `abs`, `fib`, chamada entre funções,
variável local escondendo global), equivalência semântica entre o
código gerado e o interpretador (um simulador de máquina que modela a
pilha do sistema como memória endereçável de verdade, com `%rsp`/`%rbp`
como inteiros, suportando `call`/`ret` com pilha de retorno própria),
e o comportamento do CLI via subprocess (incluindo compilação de uma
função recursiva).

## Exemplos fornecidos

| Arquivo | Conteúdo | Resultado |
|---|---|---|
| `valido1.fun` | `abs(0 - 42)` (exemplo do enunciado) | `42` |
| `valido2.fun` | `fib(10)` recursivo (exemplo do enunciado) | `89` |
| `valido3.fun` | `somaDosQuadrados(3, 4)`, chamando `quadrado()` duas vezes | `25` |
| `valido4.fun` | `dobro(5) + x`, com parâmetro `x` da função escondendo o `x` global | `110` |
| `invalido_funcao_nao_declarada.fun` | Chamada a função nunca declarada | erro semântico, exit 1 |
| `invalido_numero_de_parametros.fun` | Chamada com número de argumentos diferente do declarado | erro semântico, exit 1 |
| `invalido_variavel_fora_de_escopo.fun` | Uso, em `main`, de uma variável local de outra função | erro semântico, exit 1 |

## Itens deliberadamente fora de escopo

- **Funções mutuamente recursivas** — mencionadas explicitamente no
  enunciado como exercício opcional, não como parte do artefato
  mínimo. A implementação processa declarações sequencialmente e
  rejeita (corretamente) uma função que chame outra declarada
  **depois** dela no texto — comportamento coberto por um teste
  dedicado (`test_funcao_mutuamente_recursiva_e_rejeitada`).
- **Funções locais** (funções declaradas dentro de outras funções) —
  não fazem parte da gramática de Fun.
- Nenhuma variação sintática das atividades anteriores foi revisitada
  (operadores `<=`/`>=`, booleanos, etc.) — fora de escopo também.
