# Compilador EV (Atividade 08)

Compilador completo para a linguagem **EV** (Expressões com Variáveis),
que estende EC2 (Atividade 07) com declaração e uso de variáveis. Um
programa EV é uma sequência de zero ou mais declarações
(`nome = expressao;`), seguida de uma expressão final obrigatória
(`= expressao`), cujo resultado é o resultado do programa.

Exemplo (perímetro de um retângulo):

```
l = 30;
c = 40;
= l + l + c + c
```

Cada declaração pode usar qualquer variável já declarada antes dela; a
expressão final pode usar qualquer variável declarada no programa
inteiro. Usar uma variável que não foi declarada é um **erro
semântico**.

Gramática:

```
<programa> ::= <decl>* <result>
<decl>     ::= <ident> '=' <exp> ';'
<ident>    ::= <letra><letra_digito>*
<result>   ::= '=' <exp>
<exp>      ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m>    ::= <prim> (('*' | '/') <prim>)*
<prim>     ::= <num> | <ident> | '(' <exp> ')'
```

## Requisitos

- Python 3.8 ou superior, sem dependências externas.
- Para montar e linkar o `.s` gerado: GNU Assembler (`as`) e linker
  (`ld`) em um ambiente Linux x86-64 (no Windows, use o WSL). O
  `runtime.s` (fornecido neste diretório) precisa estar visível para o
  `as` durante a montagem.

## Como usar

A partir desta pasta:

```sh
python compev.py <arquivo.ev>
```

O compilador grava a saída no mesmo diretório da entrada, trocando a
extensão `.ev` por `.s`. Exemplo:

```sh
python compev.py exemplos/valido2.ev
# gera exemplos/valido2.s
```

Em caso de erro léxico, sintático **ou semântico** (uso de variável não
declarada), encerra com exit code 1, mensagem em `stderr` e nenhum `.s`
é gravado.

## Montar e executar o `.s` gerado

```sh
python compev.py exemplos/valido2.ev
as --64 -o exemplos/valido2.o exemplos/valido2.s
ld -o exemplos/valido2 exemplos/valido2.o
./exemplos/valido2
# imprime: 60467
```

## Estrutura

```
compilador-ev/
├── lexer.py           # estendido: IDENT, IGUAL, PONTO_VIRGULA
├── ast_ev.py          # Exp, Const, OpBin, Op, Var, Decl, Programa
├── parser.py          # programa / decl / exp / exp_m / prim
├── semantica.py         # TabelaSimbolos, verifica_programa
├── codegen.py         # secao .bss + mov de/para variaveis
├── compev.py          # CLI: lex -> parse -> semantica -> codegen
├── runtime.s          # reusado sem alteração (Atividade 02/06/07)
├── exemplos/
│   ├── valido1.ev     # perímetro do retângulo (enunciado)              -> 140
│   ├── valido2.ev     # exemplo completo do enunciado                   -> 60467
│   ├── valido3.ev     # sem nenhuma declaração                          -> 42
│   ├── valido4.ev     # reatribuição da mesma variável                  -> 15
│   ├── invalido_uso_antes_da_declaracao.ev
│   ├── invalido_variavel_nao_declarada.ev
│   └── invalido_erro_lexico_num_letra.ev
├── tests/test_ev.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

## O pipeline agora tem 4 etapas

```
código-fonte → [Análise Léxica] → tokens → [Análise Sintática] → AST
             → [Análise Semântica] → AST (verificada) → [Geração de Código] → .s
```

A etapa nova é a **análise semântica**: depois que o parser monta a
árvore inteira, `semantica.verifica_programa()` percorre as
declarações na ordem do código-fonte, usando uma **tabela de
símbolos** (`TabelaSimbolos`) para checar que toda `Var` referenciada
já foi declarada antes. O processo para no primeiro erro encontrado.

## Testes

```sh
python tests/test_ev.py
```

32 testes em 7 classes: léxico (tokens novos e o erro léxico de dígito
seguido de letra), parser (estrutura da AST), erros sintáticos, análise
semântica (os dois erros do exemplo do enunciado + casos válidos),
interpretação (`Programa.avaliar()`), equivalência semântica entre o
código gerado e o interpretador (simulador de máquina de pilha
estendido com memória para variáveis), e o comportamento do CLI via
subprocess.

## Exemplos fornecidos

| Arquivo | Conteúdo | Resultado |
|---|---|---|
| `valido1.ev` | `l=30; c=40; = l+l+c+c` | `140` |
| `valido2.ev` | `x=(7+4)*12; y=x*3+11; = (x*y)+(x*11)+(y*13)` | `60467` |
| `valido3.ev` | `= 6 * 7` (sem declarações) | `42` |
| `valido4.ev` | `x=10; x=x+5; = x` (reatribuição) | `15` |
| `invalido_uso_antes_da_declaracao.ev` | `x=7+y; y=x*11; = x*y+z` | erro semântico (`y`), exit 1 |
| `invalido_variavel_nao_declarada.ev` | `x=7*8; = x+w` | erro semântico (`w`), exit 1 |
| `invalido_erro_lexico_num_letra.ev` | `= 237axy` | erro léxico, exit 1 |

## Variação sintática

Seguimos exatamente a sintaxe proposta no enunciado (seção 2), sem
adotar nenhuma das variações citadas na seção 7 (palavra-chave
`return`, sintaxe estilo Pascal ou estilo C) — apresentadas no
enunciado como opcionais.
