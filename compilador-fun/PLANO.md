# Plano de Implementação — Atividade 10

**Objetivo:** estender o compilador Cmd (Atividade 09) para a linguagem
**Fun**, adicionando declaração e chamada de funções — com parâmetros,
variáveis locais e recursão (direta) — usando a pilha do sistema e uma
convenção de chamada baseada em `CALL`/`RET` e *frame pointer* (`RBP`).

## Gramática alvo (do enunciado)

```
<programa> ::= <decl>* 'main' '{' <cmd>* 'return' <exp> ';' '}'
<decl>     ::= <vardecl> | <fundecl>
<fundecl>  ::= 'fun' <ident> '(' <arglist>? ')'
               '{' <vardecl>* <cmd>* 'return' <exp> ';' '}'
<arglist>  ::= <ident> | <ident> ',' <arglist>
<vardecl>  ::= 'var' <ident> '=' <exp> ';'
<cmd>      ::= <if> | <while> | <atrib>
<if>       ::= 'if' <exp> '{' <cmd>* '}' 'else' '{' <cmd>* '}'
<while>    ::= 'while' <exp> '{' <cmd>* '}'
<atrib>    ::= <ident> '=' <exp> ';'
<exp>      ::= <exp_a> (('<' | '>' | '==') <exp_a>)*
<exp_a>    ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m>    ::= <prim> (('*' | '/') <prim>)*
<prim>     ::= <num> | <ident> | '(' <exp> ')' | <fun>
<fun>      ::= <ident> '(' <params>? ')'
<params>   ::= <exp> | <exp> ',' <params>
```

Um programa Fun é zero ou mais declarações (de variáveis globais —
agora marcadas com `var` — ou de funções, marcadas com `fun`), seguidas
do bloco principal marcado por `main`. Variáveis locais e parâmetros
são visíveis só dentro da função onde aparecem, e escondem uma
variável global de mesmo nome.

## O que muda em relação à Atividade 09 (Cmd)

Igual às Atividades 08 e 09, **todos os estágios** mudam:

| Componente | Ação |
|---|---|
| `lexer.py` | **Estendido**: token `VIRGULA` (`,`) e as palavras-chave `fun`, `var`, `main`. |
| `ast_fun.py` | **Estendido**: `Exp`/`Const`/`Var`/`OpBin` reaproveitados; novo nó `Chamada` (chamada de função, como expressão primária); `VarDecl` e `FunDecl` (com parâmetros, variáveis locais próprias, comandos e expressão final); `Programa` com declarações + bloco `main`. |
| `parser.py` | **Estendido**: `decl` agora escolhe entre `vardecl`/`fundecl` por *peek* na palavra-chave; `prim` decide entre `Var` e `Chamada` olhando o token **depois** do identificador (se for `(`, é chamada). |
| `semantica.py` | **Estendido**: tabela de símbolos com dois namespaces (variáveis globais e funções com sua aridade); cada função tem seu próprio conjunto de nomes locais (parâmetros + `var` locais). Função é registrada **antes** de verificar seu próprio corpo, para permitir recursão direta. |
| `codegen.py` | **Estendido**: convenção de chamada com pilha — parâmetros empilhados em ordem inversa antes do `call`; prólogo/epílogo de função com `push %rbp`/`sub`/`mov %rsp,%rbp` e `add $8*L,%rsp`/`pop %rbp`/`ret`; acesso a variável local/parâmetro via deslocamento de `%rbp`. |
| `compfun.py` | Novo ponto de entrada, mesma estrutura das atividades anteriores. |
| `runtime.s` | Reusado sem alteração. |

## Análise léxica

Só um token novo, a vírgula (`VIRGULA`), usada para separar parâmetros
formais (`fun f(x, y)`) e parâmetros reais (`f(1, 2)`). Três palavras-
chave novas: `fun`, `var`, `main` — reconhecidas com a mesma técnica já
usada para `if`/`else`/`while`/`return` desde a Atividade 09 (compara o
lexema do identificador contra uma tabela fixa só depois de montar o
lexema completo).

## Análise sintática

Dois pontos exigem atenção (seção 4 do enunciado), ambos resolvidos com
*peek* de 1 token, sem nenhuma técnica nova:

1. **Lista de parâmetros** (formais e reais) — reconhecida em laço,
   olhando o próximo token até encontrar `)`.
2. **Referência a variável vs. chamada de função** — os dois começam
   com um identificador; o parser olha o token **seguinte**: se for
   `(`, é uma chamada de função (`Chamada`); caso contrário, é uma
   referência a variável (`Var`).

## Análise semântica

Duas verificações novas, além da já existente para variáveis (seção 5
do enunciado):

1. **Chamada de função** — verifica que a função foi declarada (existe
   na tabela como função, não como variável) e que o número de
   parâmetros reais bate com o número de parâmetros formais.
2. **Escopo de variáveis dentro de funções** — a tabela de símbolos
   ganha um namespace de **variáveis locais por função** (parâmetros +
   `var` locais), consultado **antes** do namespace global; se não
   encontrar localmente, cai para o global. Isso implementa
   corretamente a regra de que uma variável local esconde uma global de
   mesmo nome.

**Recursão direta**: a função é registrada na tabela **antes** de seu
próprio corpo ser verificado, exatamente como o enunciado descreve com
o exemplo de `fib`. Como as declarações são processadas sequencialmente
(uma função só pode chamar funções declaradas antes dela, exceto a si
mesma), **funções mutuamente recursivas não são suportadas** — o
enunciado explicitamente trata isso como esperado, não como bug, e
menciona a extensão como exercício opcional que não implementamos.

## Geração de código

Adotamos exatamente a convenção de chamada descrita no enunciado
(seção 6.1), com a pilha do sistema para parâmetros e variáveis locais
e `%rax` para o valor de retorno:

### Chamada de função

1. Calcula e empilha cada parâmetro real, na **ordem inversa** (último
   parâmetro primeiro): `código(argN) → push %rax → ... → código(arg1)
   → push %rax`.
2. `call <nome_da_funcao>`.
3. Remove os parâmetros da pilha: `add $8*N, %rsp` (pulado quando a
   função não tem parâmetros).

### Prólogo e epílogo da função (com L variáveis locais)

```
<nome>:
    push %rbp
    sub $8*L, %rsp      # pulado se L == 0
    mov %rsp, %rbp
    <código de cada variável local, gravando em deslocamento(%rbp)>
    <código dos comandos>
    <código da expressão de resultado, deixa o valor em %rax>
    add $8*L, %rsp      # pulado se L == 0
    pop %rbp
    ret
```

Seguimos literalmente as duas instruções do epílogo sugeridas na
seção 6.1.4 do enunciado (`add $8*L, %rsp` seguido de `pop %rbp`), em
vez da instrução `leave` do x86-64. Chegamos a experimentar `leave`
(que equivale a `mov %rbp, %rsp; pop %rbp`) por parecer mais direta,
mas os testes de equivalência semântica (seção "Testes planejados")
expuseram que ela é **incorreta** para a convenção de prólogo adotada
aqui: como o prólogo faz `push %rbp` **antes** do `sub` e só copia
`%rsp` para `%rbp` **depois** dele, `%rbp` acaba apontando para o
início do bloco de variáveis locais, não para o slot onde o `%rbp`
antigo foi salvo (esse slot fica `8*L` bytes acima). `leave` assume a
convenção clássica em que `%rbp` aponta diretamente para esse slot —
válida apenas quando `L == 0` — e por isso corrompia o `%rbp` restaurado
sempre que a função tinha alguma variável local. Ver a seção "Decisões
de projeto" do relatório para o relato completo do bug e de como foi
encontrado.

### Deslocamentos no registro de ativação

Para uma função com `L` variáveis locais (declaradas na ordem
`v_0, v_1, ..., v_{L-1}`) e `P` parâmetros (declarados na ordem
`p_0, p_1, ..., p_{P-1}`):

- variável local `v_j` → deslocamento `8*j` a partir de `%rbp`
  (a primeira variável local fica em `0(%rbp)`);
- parâmetro `p_i` → deslocamento `8*L + 16 + 8*i` a partir de `%rbp`
  (os `16` cobrem o `%rbp` salvo e o endereço de retorno empilhados
  pelo prólogo/`call`).

Essas fórmulas reproduzem exatamente os deslocamentos do exemplo da
seção 6.1.3 do enunciado (`b` em `8(%rbp)`, `y` em `40(%rbp)` para uma
função com 2 locais e 2 parâmetros).

### Variáveis: locais vs. globais

O gerador de código mantém um mapa `nome → deslocamento` **enquanto
gera o código de uma função específica**; fora desse contexto (bloco
`main`), o mapa é vazio e toda referência a variável usa o símbolo
`.bss` global, exatamente como na Atividade 09.

### Modelo de saída (seção 7 do enunciado)

O arquivo `.s` agora tem três partes: seção `.bss` (variáveis globais),
o bloco principal (rótulo `_start`, terminando em `call imprime_num` /
`call sair`), e o código de cada função (rótulo com o nome da função,
prólogo, corpo, epílogo) — nessa ordem, antes do `.include "runtime.s"`.

## Estrutura dos arquivos

```
compilador-fun/
├── lexer.py           # estendido: VIRGULA, fun/var/main
├── ast_fun.py         # Exp/Const/Var/OpBin/Chamada + Cmd/Atrib/If/While
│                       # + VarDecl/FunDecl/Programa
├── parser.py          # decl (vardecl|fundecl) / arglist / params / fun
├── semantica.py        # TabelaSimbolos (globais + locais por funcao)
├── codegen.py         # convencao de chamada: push/call/cleanup, prologo/epilogo
├── compfun.py         # CLI: lex -> parse -> semantica -> codegen
├── runtime.s          # reusado sem alteracao
├── exemplos/
│   ├── valido1.fun    # abs() (exemplo do enunciado)
│   ├── valido2.fun    # fib() recursiva (exemplo do enunciado)
│   ├── valido3.fun    # funcao chamando outra funcao
│   ├── valido4.fun    # variavel local esconde global de mesmo nome
│   ├── invalido_funcao_nao_declarada.fun
│   ├── invalido_numero_de_parametros.fun
│   └── invalido_variavel_fora_de_escopo.fun
├── tests/
│   └── test_fun.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

## Testes planejados

- **Léxico**: token de vírgula; as três palavras-chave novas.
- **Sintático**: `FunDecl` com zero, um e vários parâmetros; `Chamada`
  reconhecida corretamente vs. `Var` (`f` vs. `f()`); lista de
  parâmetros com vírgula.
- **Semântico**: chamada de função não declarada; número de parâmetros
  errado; variável local usada fora da função onde foi declarada;
  variável local escondendo uma global de mesmo nome; chamada
  recursiva direta permitida.
- **Interpretação** (`Programa.avaliar()`): `abs(-5)` e `abs(5)`;
  `fib(n)` para vários `n`; função que chama outra função; variável
  local escondendo global.
- **Geração de código / equivalência semântica**: estendemos o
  simulador de máquina de pilha da Atividade 09 (que já tinha *program
  counter*, rótulos e desvios) com suporte a **`call`/`ret`** (uma
  pilha de retorno própria) e **memória de pilha endereçável por
  deslocamento de `%rbp`** (para variáveis locais/parâmetros), e
  comparamos o resultado com `avaliar()` para os mesmos programas —
  incluindo a função recursiva `fib`.
- **CLI**: `compfun.py` grava `.s` para entrada válida; erro léxico,
  sintático ou semântico produz exit 1 sem gravar `.s`.

## Itens deliberadamente fora de escopo

- **Funções mutuamente recursivas** — mencionado explicitamente no
  enunciado (seção 5.1) como exercício opcional, não como parte do
  artefato mínimo. Nossa implementação processa declarações
  sequencialmente e rejeita (corretamente) uma função que chame outra
  declarada **depois** dela no texto.
- **Funções locais** (funções declaradas dentro de outras funções) —
  não fazem parte da gramática de Fun.
- Nenhuma variação sintática das atividades anteriores foi revisitada
  (operadores `<=`/`>=`, booleanos, etc.) — fora de escopo desta
  atividade também.

## Validação

- `python tests/test_fun.py` roda toda a suíte sem falhas.
- `python compfun.py exemplos/valido2.fun` (Fibonacci recursivo) gera
  `.s` que, montado e executado, produz o valor esperado.
- `python compfun.py exemplos/invalido_numero_de_parametros.fun`
  encerra com exit 1 e mensagem clara no `stderr`, sem gerar `.s`.
