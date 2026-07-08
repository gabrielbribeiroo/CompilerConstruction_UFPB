# Plano de Implementação — Atividade 08

**Objetivo:** estender o compilador EC2 (Atividade 07) para a linguagem
**EV** (Expressões com Variáveis): declaração e uso de variáveis, uma
nova etapa de **análise semântica** com tabela de símbolos, e geração
de código que reserva memória para as variáveis (seção `.bss`).

## Gramática alvo (do enunciado)

```
<programa> ::= <decl>* <result>
<decl>     ::= <ident> '=' <exp> ';'
<ident>    ::= <letra><letra_digito>*
<result>   ::= '=' <exp>
<exp>      ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m>    ::= <prim> (('*' | '/') <prim>)*
<prim>     ::= <num> | <ident> | '(' <exp> ')'
<num>      ::= <digito><digito>*
```

Um programa é zero ou mais declarações (`ident = exp;`) seguidas de uma
expressão final obrigatória (`= exp`). Cada declaração pode usar
qualquer variável já declarada antes dela; a expressão final pode usar
qualquer variável declarada no programa inteiro.

## O que muda em relação à Atividade 07 (EC2)

Diferente da Atividade 07 (onde geração de código e AST eram idênticos
à atividade anterior), aqui o enunciado pede mudança em **todos** os
estágios:

| Componente | Ação |
|---|---|
| `lexer.py` | **Estendido**: três tokens novos — `IDENT` (identificador), `IGUAL` (`=`), `PONTO_VIRGULA` (`;`). |
| `ast_ev.py` | **Estendido**: além de `Exp`/`Const`/`OpBin`/`Op` (mesma forma da Atividade 05-07), adiciona `Var` (referência a variável), `Decl` (declaração) e `Programa` (nó raiz com lista de declarações + expressão final). |
| `parser.py` | **Reescrito**: novo não-terminal `programa` no topo, `decl`, e `prim` estendido para reconhecer identificadores. `exp`/`exp_m` mantêm a mesma estrutura da Atividade 07. |
| `semantica.py` | **Novo módulo**: análise semântica / verificação de variáveis usando uma tabela de símbolos. |
| `codegen.py` | **Estendido**: variáveis viram símbolos `.lcomm` na seção `.bss`; o corpo do programa agora inclui o código de cada declaração (terminando em `mov %rax, <var>`) seguido do código da expressão final. |
| `compev.py` | Novo ponto de entrada: lex → parse → **análise semântica** → codegen. |
| `runtime.s` | Reusado sem alteração (mesmo arquivo desde a Atividade 02/06/07). |

## Análise léxica

Um identificador começa com uma letra (`a-z`, `A-Z`) e é seguido de
zero ou mais letras ou dígitos. Conforme o enunciado (seção 3), uma
sequência de dígitos seguida imediatamente por uma letra sem separador
(ex.: `237axy`) continua sendo um **erro léxico** — o lexer reconhece os
dígitos como início de um `NUMERO`, e ao encontrar uma letra logo em
seguida (sem espaço/operador entre eles), sinaliza erro na posição da
letra, em vez de silenciosamente cortar em dois tokens (`237` e `axy`).

## Árvore de sintaxe abstrata

Reaproveitamos a base `Exp`/`Const`/`OpBin`/`Op` das atividades
anteriores (mesma estrutura, `dataclass(frozen=True)`), e adicionamos:

- **`Var(nome: str)`** — folha que representa uma referência a uma
  variável.
- **`Decl(nome: str, exp: Exp)`** — não é uma `Exp`; representa uma
  declaração `nome = exp;`.
- **`Programa(declaracoes: list[Decl], exp_final: Exp)`** — nó raiz.

`avaliar()` passa a receber um **ambiente** (`env: dict[str, int]`)
para poder resolver o valor de uma `Var`; `Const` e `OpBin` apenas
repassam o ambiente recursivamente.

## Análise sintática

Implementação direta do pseudocódigo do enunciado (seção 4):

- `analisa_programa()` — enquanto o próximo token (via *peek*) for
  `IDENT`, reconhece uma declaração; ao encontrar `IGUAL`, reconhece a
  expressão final e monta o nó `Programa`.
- `_analisa_decl()` — consome o identificador, exige `=`, reconhece a
  expressão, exige `;`.
- `_analisa_exp_a()` / `_analisa_exp_m()` — exatamente a mesma
  estrutura da Atividade 07 (precedência + associatividade à
  esquerda via laço).
- `_analisa_prim()` — estendida: além de `NUMERO` e `(exp)`, agora
  também reconhece `IDENT`, devolvendo um nó `Var`.

## Análise semântica (verificação de variáveis)

Módulo novo `semantica.py`:

- **`TabelaSimbolos`** — envolve um `set[str]` com os nomes já
  declarados; método `declarar(nome)` e `esta_declarada(nome)`.
- **`verifica_programa(programa)`** — percorre as declarações **na
  ordem em que aparecem no código-fonte**: para cada declaração,
  verifica que toda `Var` referenciada na expressão já está na tabela
  de símbolos (senão, `ErroSemantico`); só então declara a variável
  correspondente. Ao final, verifica a expressão de resultado da mesma
  forma. O processo para no primeiro erro encontrado, conforme
  descrito na seção 5 do enunciado ("o compilador deve reportar um
  erro e parar o processo").

## Geração de código

Estende o esquema de pilha já usado nas Atividades 06-07
(`Const`/`OpBin` inalterados na essência) com:

- **`Var`** → `mov <nome>, %rax` (lê da memória para o registrador).
- **Seção `.bss`** — uma diretiva `.lcomm <nome>, 8` por variável
  declarada (8 bytes = inteiro de 64 bits), sem duplicar entradas
  mesmo que uma variável seja reatribuída mais de uma vez.
- **Código de cada declaração** — o código da expressão do lado
  direito, seguido de `mov %rax, <nome>` (grava o resultado na
  variável).
- **Modelo de saída** — agora tem duas partes preenchidas: a seção
  `.bss` (variáveis) e a seção `.text` (código de cada declaração, em
  ordem, seguido do código da expressão final), exatamente como no
  modelo da seção 6 do enunciado.

## Variação sintática

Optamos por seguir **exatamente** a sintaxe proposta no enunciado
(seção 2, com `=` tanto para atribuição quanto para marcar a expressão
final), sem adotar nenhuma das variações da seção 7 (palavra-chave
`return`, estilo Pascal, estilo C). A sintaxe do enunciado já é
simples de tokenizar e simples de analisar, e as variações são
apresentadas como opcionais ("de acordo com o interesse do grupo").

## Estrutura dos arquivos

```
compilador-ev/
├── lexer.py           # estendido: IDENT, IGUAL, PONTO_VIRGULA
├── ast_ev.py          # Exp, Const, OpBin, Op, Var, Decl, Programa
├── parser.py          # NOVO: programa / decl / exp / exp_m / prim
├── semantica.py        # NOVO: TabelaSimbolos, verifica_programa
├── codegen.py         # estendido: secao .bss, mov de/para variaveis
├── compev.py          # ponto de entrada: lex -> parse -> semantica -> codegen
├── runtime.s          # reusado sem alteracao
├── exemplos/
│   ├── valido1.ev     # perimetro do retangulo (exemplo do enunciado)
│   ├── valido2.ev     # exemplo completo do enunciado (resultado 60467)
│   ├── valido3.ev     # sem nenhuma declaracao (so a expressao final)
│   ├── valido4.ev     # reatribuicao da mesma variavel
│   ├── invalido_uso_antes_da_declaracao.ev
│   ├── invalido_variavel_nao_declarada.ev
│   └── invalido_erro_lexico_num_letra.ev
├── tests/
│   └── test_ev.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

## Testes planejados

- **Léxico**: tokens `IDENT`, `IGUAL`, `PONTO_VIRGULA`; erro léxico
  para `237axy`.
- **Sintático**: estrutura da AST (`Programa` com lista de `Decl` e
  `exp_final`) para programas com zero, uma e várias declarações;
  `Var` reconhecida como `prim`; erros sintáticos (declaração sem
  `;`, programa sem expressão final, etc.).
- **Semântico**: os dois erros do exemplo do enunciado (uso de
  variável antes de sua própria declaração, uso de variável nunca
  declarada na expressão final) devem ser detectados; programas
  válidos passam sem erro.
- **Interpretação** (`avaliar(env)`): o exemplo do enunciado deve
  avaliar para `60467`; o exemplo do perímetro deve avaliar para `140`.
- **Geração de código / equivalência semântica**: reaproveitamos a
  técnica das Atividades 06-07 — um simulador da máquina de pilha em
  Python, agora estendido com um dicionário de memória para simular
  `.bss`, compara o resultado do código gerado com `avaliar(env)` do
  interpretador para vários programas.
- **CLI**: `compev.py` grava `.s` para entrada válida; erro léxico,
  sintático ou semântico produz exit 1, mensagem em `stderr`, sem
  gravar `.s`.

## Itens deliberadamente fora de escopo

- Nenhuma das variações sintáticas da seção 7 (palavra-chave `return`,
  sintaxe estilo Pascal ou C) foi implementada — são citadas no
  enunciado como opcionais, "de acordo com o interesse do grupo".
- Verificação de tipos: o próprio enunciado (seção 5) diz que não é
  necessária em EV, já que todas as variáveis têm o mesmo tipo.
- A permissão de algumas linguagens de "usar uma variável declarada
  mais adiante no programa" (mencionada entre parênteses na seção 5)
  é explicitamente apresentada como comportamento de *outras*
  linguagens, não como requisito de EV — nossa implementação segue a
  regra de EV (uso só depois da declaração).

## Validação

- `python tests/test_ev.py` roda toda a suíte sem falhas.
- `python compev.py exemplos/valido2.ev` gera `.s` que, montado e
  executado, imprime `60467`.
- `python compev.py exemplos/invalido_variavel_nao_declarada.ev`
  encerra com exit 1 e mensagem clara no `stderr`, sem gerar `.s`.
