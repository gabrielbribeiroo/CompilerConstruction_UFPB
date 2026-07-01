# Relatório de Implementação — Atividade 07: Compilador EC2 (Precedência)

**Universidade Federal da Paraíba (UFPB)**
**Centro de Informática — Curso de Ciência da Computação**
**Disciplina:** Construção de Compiladores 1
**Professor:** Andrei de Araújo Formiga

## Integrantes do grupo

| Nome                                       | Matrícula     |
| ------------------------------------------ | ------------- |
| Davi Alves Rodrigues                       | 20230102377   |
| Gabriel Barbosa Ribeiro de Oliveira        | 20230012814   |
| João Vitor Sampaio Costa                   | 20230089776   |
| Nathan Meira Nóbrega                       | 20240008904   |

---

## O que foi implementado

### 1. O problema: parênteses obrigatórios vs. notação natural

Em EC1, toda operação binária precisa de parênteses explícitos
(`(a op b)`), o que elimina qualquer ambiguidade mas é pouco natural para
quem está acostumado com a notação matemática usual, onde `7 + 5 * 3`
significa `7 + (5 * 3)` por convenção de precedência. O objetivo desta
atividade é fazer o analisador sintático aceitar expressões nessa
notação mais natural, sem exigir parênteses em toda operação.

Simplesmente remover os parênteses da gramática de EC1
(`<exp> ::= <exp> <op> <exp>`) não funciona por dois motivos discutidos
no enunciado:

1. **Ambiguidade de precedência** — sem distinguir níveis, `7 + 5 * 3`
   teria duas árvores de derivação possíveis, uma calculando a soma
   primeiro e outra a multiplicação primeiro.
2. **Recursão à esquerda** — a produção `<exp> ::= <exp> <op> <exp>`,
   mesmo com níveis de precedência separados, gera uma função de parser
   que chama a si mesma como primeira ação (`exp(): e1 = exp(); ...`),
   resultando em loop infinito em um parser descendente recursivo.

### 2. Gramática EC2

A gramática usada, exatamente a do enunciado (seção 3), resolve os dois
problemas simultaneamente: introduz um não-terminal por nível de
precedência (resolve a ambiguidade) e usa a forma iterativa `(...)* `
em vez de recursão à esquerda direta (resolve o loop infinito e mantém
associatividade à esquerda — ao contrário de simplesmente inverter a
ordem para `<termo> '+' <exp>`, que geraria associatividade à *direita*
e quebraria a semântica de `-` e `/`):

```
<exp_a> ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m> ::= <prim>  (('*' | '/') <prim>)*
<prim>  ::= <num> | '(' <exp_a> ')'
```

`exp_a` é o nível aditivo (precedência mais baixa), `exp_m` o
multiplicativo (precedência mais alta), e `prim` reconhece uma constante
ou reinicia a análise em `exp_a` dentro de parênteses.

### 3. Parser (`parser.py`) — reescrito

Implementamos uma função por não-terminal, seguindo o pseudocódigo do
enunciado (seção 3) ao pé da letra:

- **`_analisa_exp_a()`** — reconhece um `exp_m` (operando esquerdo com
  `_analisa_exp_m()`), depois entra num laço: enquanto o próximo token
  (via `olhar_proximo()`, sem consumir) for `+` ou `-`, consome o
  operador, reconhece outro `exp_m`, e monta
  `esq = OpBin(op, esq, dir)` — o nó recém-criado vira o novo operando
  esquerdo da próxima iteração, o que produz associatividade à
  esquerda automaticamente, sem pós-processamento na árvore.
- **`_analisa_exp_m()`** — estrutura idêntica a `_analisa_exp_a`, mas
  para `*`/`/`, chamando `_analisa_prim()` em vez de `_analisa_exp_m()`.
- **`_analisa_prim()`** — se o próximo token for `NUMERO`, devolve
  `Const`; se for `PAREN_ESQ`, consome, chama `_analisa_exp_a()`
  recursivamente (reiniciando no nível de precedência mais baixo dentro
  dos parênteses) e exige `PAREN_DIR` ao final.
- **`analisa_programa()`** — chama `_analisa_exp_a()` e exige `EOF` em
  seguida, mesmo invariante usado desde a Atividade 05 para capturar
  lixo após a expressão raiz.

O ponto de atenção citado no enunciado — "não retirar o token do fluxo
de entrada ao verificar se é operador" — já estava resolvido, porque o
`lexer.py` reusado (sem alteração) já expõe `olhar_proximo()` desde a
Atividade 04/05 especificamente para esse tipo de decisão por
*lookahead* sem consumo.

### 4. Reuso sem alteração de lexer, AST e codegen

Confirmado com `diff` byte a byte: `lexer.py`, `ast_ec1.py`,
`codegen.py` e `runtime.s` neste diretório são **idênticos** aos da
Atividade 06. Isso é intencional e reflete diretamente o que o
enunciado pede na seção 4 ("Artefato para entrega"): *"A geração de
código não muda com relação à Atividade 06."* A árvore de sintaxe
abstrata (`Exp`, `Const`, `OpBin`, `Op`) também não precisa mudar —
só muda **como** ela é construída, não sua representação. O analisador
léxico já reconhecia todos os tokens necessários (`NUMERO`,
`PAREN_ESQ`, `PAREN_DIR`, `SOMA`, `SUB`, `MULT`, `DIV`) desde a
Atividade 04.

### 5. Ponto de entrada (`compec2.py`)

Estrutura idêntica ao `compec1.py` da Atividade 06 — apenas troca o
import de `parser` (agora o de EC2) e a extensão reconhecida
(`.ec2` → `.s`). Erros léxicos, sintáticos ou de E/S vão para `stderr`
com exit code 1, sem gerar `.s`.

### 6. Suíte de testes (`tests/test_parser_precedencia.py`)

**26 testes, 0 falhas**, em 6 classes:

| Classe | Foco | Casos |
| --- | --- | ---: |
| `TestPrecedencia` | `*`/`/` calculados antes de `+`/`-`; parênteses sobrepõem a precedência padrão | 6 |
| `TestAssociatividade` | Associatividade à esquerda em `+`, `-`, `*`, `/`, e em cadeias longas | 5 |
| `TestCompatibilidadeComEC1` | Programas EC1 (parênteses obrigatórios) continuam aceitos e avaliando igual | 5 |
| `TestErrosSintaticos` | Detecção de entrada mal formada | 7 |
| `TestEquivalenciaSemantica` | Código gerado (`codegen.py` inalterado) bate com `avaliar()` para 13 programas | 1 |
| `TestCLI` | Comportamento de `compec2.py` como subprocesso | 2 |

Destaques:

- `test_soma_e_multiplicacao_estrutura` verifica que a AST de
  `7 + 5 * 3` é exatamente
  `OpBin(SOMA, Const(7), OpBin(MULT, Const(5), Const(3)))` — não a
  árvore alternativa que calcularia a soma primeiro.
- `test_subtracao_associa_a_esquerda_estrutura` e
  `test_divisao_associa_a_esquerda_estrutura` verificam a árvore
  literal de `10 - 8 - 2` e `100 / 10 / 2`, garantindo que a
  associatividade está correta na estrutura, não só coincidindo no
  valor final por acaso.
- `TestEquivalenciaSemantica` reaproveita a técnica da Atividade 06 —
  um simulador da máquina de pilha em Python que interpreta as
  instruções emitidas pelo `codegen.py` — para confirmar que o mesmo
  gerador de código, sem nenhuma alteração, continua correto quando
  alimentado com árvores produzidas pelo novo parser de precedência.

### 7. Arquivos de exemplo

Seis programas válidos e um inválido em `exemplos/`, cobrindo
precedência (`7 + 5 * 3`), parênteses sobrepondo a precedência padrão
(`(7 + 5) * 3`), associatividade em subtração e divisão
(`10 - 8 - 2`, `100 / 10 / 2`), uma expressão mista com os quatro
operadores (`2 + 3 * 4 - 10 / 5`), compatibilidade retroativa com um
programa EC1 do enunciado da Atividade 04 (`(33 + (912 * 11))`), e um
erro sintático proposital (`7 + * 3`, operador sem operando).

---

## Estrutura de arquivos entregue

```
compilador-ec2/
├── lexer.py           # idêntico à Atividade 06
├── ast_ec1.py         # idêntico à Atividade 06
├── parser.py          # NOVO
├── codegen.py         # idêntico à Atividade 06
├── compec2.py
├── runtime.s          # idêntico à Atividade 06
├── exemplos/
│   ├── valido1.ec2
│   ├── valido2.ec2
│   ├── valido3.ec2
│   ├── valido4.ec2
│   ├── valido5.ec2
│   ├── valido6.ec2
│   └── invalido1.ec2
├── tests/
│   └── test_parser_precedencia.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

---

## Decisões de projeto

**Por que a forma `(...)* ` em vez de recursão à direita
(`<termo> '+' <exp>`)?**
A recursão à direita resolveria o loop infinito, mas geraria
associatividade à direita, que é semanticamente errada para `-` e `/`:
`10 - 8 - 2` viraria `10 - (8 - 2) = 4` em vez do correto `0`. A forma
iterativa do enunciado, onde o nó recém-criado vira o novo operando
esquerdo a cada iteração do laço, dá associatividade à esquerda
diretamente, sem exigir nenhum pós-processamento ou inversão da árvore.

**Por que usar `olhar_proximo()` (peek) em vez de consumir e "devolver"
o token se não for o esperado?**
O `AnalisadorLexico` reusado já expõe exatamente essa interface desde a
Atividade 04/05, então não havia motivo para reinventar. Consumir e
tentar "devolver" um token exigiria um mecanismo de *pushback*
adicional no lexer; o peek evita esse problema porque nunca avança o
cursor até confirmar que o token pertence à produção atual.

**Por que reusar `codegen.py` sem qualquer edição, incluindo o
comentário que ainda menciona "EC1"?**
O enunciado afirma explicitamente que a geração de código não muda em
relação à Atividade 06. Reusar o arquivo byte a byte idêntico (e
verificado com `diff`) é a demonstração mais direta de que essa
afirmação é verdadeira: o compilador EC2 herda a mesma AST e o mesmo
esquema de tradução baseado em pilha, e a única mudança de fato está
concentrada em `parser.py`. Editar o comentário só para dizer "EC2"
seria puramente cosmético e romperia essa garantia de identidade sem
nenhum ganho — por isso optamos por documentar a decisão aqui em vez
de tocar no arquivo.

**Por que os testes de estrutura da AST (não só de valor) são
importantes?**
Um teste que só verifica o valor final pode passar por acidente — por
exemplo, `7 + 5 * 3` daria `36` só se a soma fosse calculada primeiro E
o resultado fosse coincidentemente igual ao valor esperado em outro
caso. Verificar a árvore literalmente (`OpBin(SOMA, Const(7),
OpBin(MULT, Const(5), Const(3)))`) garante que a *estrutura* da
precedência e associatividade está correta, não só que o número final
bateu por coincidência aritmética.

---

## Dificuldades

Nenhuma dificuldade significativa. O pseudocódigo do enunciado (seção 3)
já descreve o parser praticamente pronto para tradução direta em
Python; o único cuidado foi generalizar a mesma estrutura de laço para
`exp_m` sem duplicar lógica desnecessária (as duas funções,
`_analisa_exp_a` e `_analisa_exp_m`, têm exatamente a mesma forma,
diferindo apenas no dicionário de operadores e na função de nível
inferior que chamam — conforme o próprio enunciado observa na seção 3).
