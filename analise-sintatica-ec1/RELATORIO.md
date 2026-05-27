# Relatório de Implementação — Atividade 05: Análise Sintática EC1

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

### 1. Árvore de sintaxe abstrata (`ast_ec1.py`)

Seguindo a sugestão da seção 5 do enunciado, a árvore é representada por uma
hierarquia de classes:

- `Exp` — classe-base abstrata. Define a interface `avaliar()` e `__str__()`.
- `Const(valor: int)` — folha que carrega o valor de uma constante inteira.
- `OpBin(op: Op, esq: Exp, dir: Exp)` — nó interno com operador e dois
  filhos (operando esquerdo e direito).
- `Op` — enumeração com os quatro operadores (`SOMA`, `SUB`, `MULT`, `DIV`),
  com `value` igual ao símbolo (`'+'`, `'-'`, `'*'`, `'/'`) para facilitar
  a reconstrução textual.

`Const` e `OpBin` são `dataclasses` com `frozen=True`. Isso fornece
automaticamente `__eq__` por valor, o que permite comparações diretas entre
ASTs nos testes (`self.assertEqual(arvore, esperado)`) sem código extra,
e também torna os nós hasháveis.

### 2. Analisador sintático descendente recursivo (`parser.py`)

A classe `AnalisadorSintatico` implementa o algoritmo descrito nas seções 3
e 6 do enunciado. Para cada não-terminal há uma função privada:

- `_analisa_exp()` — implementa a regra
  `<expressao> ::= <literal> | '(' <expressao> <operador> <expressao> ')'`.
  Consome o próximo token e ramifica:
  - se for `NUMERO`, devolve `Const(int(lexema))`;
  - se for `PAREN_ESQ`, chama `_analisa_exp()` recursivamente para o
    operando esquerdo, depois `_analisa_operador()`, depois novamente
    `_analisa_exp()` para o direito, e finalmente exige `PAREN_DIR`;
  - qualquer outra coisa é erro sintático.
- `_analisa_operador()` — implementa
  `<operador> ::= '+' | '-' | '*' | '/'` consumindo um token e mapeando-o
  para o `Op` correspondente.
- `analisa_programa()` — chama `_analisa_exp()` e, ao final, exige que o
  próximo token seja `EOF` (caso contrário, há lixo após a expressão).

Erros sintáticos são reportados via exceção `ErroSintatico`, que carrega a
posição (índice do caractere no texto-fonte, herdada do token problemático)
e uma mensagem descrevendo o que era esperado versus o que foi encontrado.

### 3. Interpretador por varredura da árvore (`avaliar()`)

Conforme sugerido na seção 8 do enunciado, o interpretador é implementado
como o método `avaliar()` na classe base `Exp`, sobrescrito nas subclasses:

- `Const.avaliar()` devolve o valor literal;
- `OpBin.avaliar()` avalia recursivamente os dois filhos e aplica o operador.

A divisão usa truncamento para zero (`int(a / b)`), coerente com a semântica
de divisão inteira de assembly — alvo das próximas atividades. Divisão por
zero levanta `ZeroDivisionError`.

### 4. Analisador léxico (`lexer.py`)

Reaproveita a estrutura da Atividade 04: `TipoToken` enum, `Token` como
`dataclass`, exceção `ErroLexico` com posição e caractere, e a classe
`AnalisadorLexico` com as duas interfaces discutidas na seção 7 do enunciado:

- `proximo_token()` — consome e retorna o próximo token;
- `olhar_proximo()` — *peek* sem consumir (usado nos testes, embora o parser
  funcione bem só com `proximo_token`).

Espaços, tabulações, quebras de linha e CR são ignorados; comentários de
linha (`# ...`) também (extensão herdada da atividade anterior).

### 5. Ponto de entrada (`ec1.py`)

Recebe o nome do arquivo `.ec1` na linha de comando, executa
**lex → parse → avalia** e imprime o valor em `stdout`. Erros de E/S,
léxicos, sintáticos e de divisão por zero vão para `stderr` com código de
saída 1.

### 6. Suíte de testes (`tests/test_parser.py`)

**34 testes, 0 falhas**, divididos em quatro classes do módulo `unittest`:

| Classe                    | Foco                                                  | Casos |
| ------------------------- | ----------------------------------------------------- | ----: |
| `TestArvoreSintatica`     | Estrutura da AST produzida pelo parser                |    11 |
| `TestInterpretador`       | Valor numérico produzido por `avaliar()`              |     9 |
| `TestErrosSintaticos`     | Detecção e reporte correto de programas mal formados  |    10 |
| `TestImpressaoCanonica`   | Reconstituição da expressão via `__str__()`           |     4 |
| **Total**                 |                                                       | **34** |

Destaques:

- O **exemplo literal do enunciado** (`(33 + (912 * 11))`) tem dois testes
  dedicados: um verifica que a AST construída é exatamente
  `OpBin(SOMA, Const(33), OpBin(MULT, Const(912), Const(11)))` e outro
  verifica que `avaliar()` devolve `10065`.
- A **expressão complexa** `((427 / 7) + (11 * (231 + 5)))` também é
  verificada estrutural e numericamente (resultado `2657`).
- Os testes de erro verificam que o `ErroSintatico` é levantado para
  parêntese não fechado, parêntese fechando inesperado, operador faltando
  ou substituído, operando faltando, entrada vazia, entrada só com espaços
  e lixo após a expressão raiz.

### 7. Arquivos de exemplo

Quatro programas válidos (`valido1.ec1` a `valido4.ec1`, cobrindo
constante simples, multiplicação simples e os dois exemplos do enunciado)
e três com erro sintático em pontos diferentes da árvore
(`invalido_parenteses.ec1`, `invalido_operador.ec1`,
`invalido_lixo_no_fim.ec1`).

---

## Estrutura de arquivos entregue

```
analise-sintatica-ec1/
├── lexer.py
├── ast_ec1.py
├── parser.py
├── ec1.py
├── tests/
│   └── test_parser.py
├── exemplos/
│   ├── valido1.ec1
│   ├── valido2.ec1
│   ├── valido3.ec1
│   ├── valido4.ec1
│   ├── invalido_parenteses.ec1
│   ├── invalido_operador.ec1
│   └── invalido_lixo_no_fim.ec1
├── README.md
├── PLANO.md
└── RELATORIO.md
```

---

## Decisões de projeto

**Por que `Const` e `OpBin` como `dataclass(frozen=True)`?**
Por dois motivos: o `__eq__` automático por valor encurta drasticamente os
testes de estrutura da AST, e `frozen=True` deixa explícito que os nós são
imutáveis — a AST construída pelo parser não é modificada por ninguém
depois disso, o que é um invariante útil para o interpretador e qualquer
estágio futuro do compilador.

**Por que `Op` como `Enum` com `value` igual ao símbolo?**
Um único valor representa "qual operador" — não há razão para misturar
isso com o tipo de token. Manter o símbolo como `value` deixa `OpBin.__str__`
trivial (`f"({self.esq} {self.op.value} {self.dir})"`) e ajuda a debugar.

**Por que `avaliar()` como método nas classes da AST, em vez de uma função
externa?**
É a abordagem sugerida pelo enunciado (seção 8) e dispensa `isinstance` /
`match` em uma função à parte. Adicionar um novo nó no futuro (por exemplo,
operação unária) exige apenas implementar `avaliar()` na nova classe.

**Por que o parser usa só `proximo_token()` (consume), sem `peek`?**
O pseudo-código do enunciado consome o próximo token e ramifica pelo tipo,
sem precisar devolvê-lo. Como o token de abertura (`PAREN_ESQ`) e o literal
não precisam ser preservados após a decisão (são "gastos" na própria
decisão), isso simplifica o código e não custa nada.

**Verificação de fim da entrada.**
`analisa_programa()` exige `EOF` após a expressão raiz para detectar
programas como `(6 * 7) 42` — entrada perfeitamente válida do ponto de
vista de `_analisa_exp()` para o trecho `(6 * 7)`, mas que tem lixo depois.
Sem essa checagem, o parser silenciaria erros desse tipo.

**Itens NÃO implementados (intencionalmente).**
O enunciado menciona na seção 9 a possibilidade de imprimir a árvore em
formato ASCII visual ou via graphviz — explicitamente como "outras
possibilidades". Esses itens não fazem parte do conjunto pedido na seção
10 (artefato para entrega) e não foram implementados. A impressão textual
simples (reconstrução da expressão entre parênteses) é implementada via
`__str__()` nas classes da AST porque é útil para testes e tem custo
desprezível.

---

## Dificuldades

Nenhuma dificuldade significativa. O pseudocódigo da seção 6 do enunciado
descreve o parser de forma quase completa; a tradução para Python foi
direta. Os únicos pontos que exigiram atenção:

- Decidir **onde** verificar o fim da entrada — a função
  `_analisa_exp` é recursiva e é chamada também a partir de si mesma, então
  fazer a verificação dentro dela quebraria os casos aninhados. A solução
  foi isolar essa verificação em `analisa_programa()`, que envolve o
  `_analisa_exp` raiz.
- Tipagem da divisão — como a linguagem só tem inteiros e as próximas
  etapas alvejam assembly inteiro, optamos por **divisão inteira com
  truncamento para zero** (`int(a / b)`) em vez de divisão real (`a / b`)
  ou divisão floor (`a // b`, que arredonda para `-inf`). O truncamento
  para zero é o que `idiv` faz em x86-64.
