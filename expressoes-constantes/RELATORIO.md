# Relatório de Implementação — Etapa 1: Análise Léxica EC1

**Disciplina:** Compiladores  
**Atividade:** 04 — Expressões Constantes 1  
**Data:** Maio de 2026

---

## O que foi implementado

### 1. Estrutura do token (`Token`, `TipoToken`)

Foi definida a enumeração `TipoToken` com oito valores:

| Enum           | Descrição              |
|----------------|------------------------|
| `NUMERO`       | Sequência de dígitos   |
| `PAREN_ESQ`    | `(`                    |
| `PAREN_DIR`    | `)`                    |
| `SOMA`         | `+`                    |
| `SUB`          | `-`                    |
| `MULT`         | `*`                    |
| `DIV`          | `/`                    |
| `EOF`          | Fim da entrada         |

A classe `Token` é um `dataclass` Python com três campos: `tipo`, `lexema` e `posicao`.
O método `__str__` produz exatamente o formato exigido pelo enunciado:

```
<ParenEsq, "(", 0>
<Numero, "33", 1>
```

A saída para o exemplo do enunciado `(33 + (912 * 11))` bate caractere a caractere com
o esperado, incluindo as posições:

```
<ParenEsq, "(", 0>    <Numero, "33", 1>    <Soma, "+", 4>
<ParenEsq, "(", 6>    <Numero, "912", 7>   <Mult, "*", 11>
<Numero, "11", 13>    <ParenDir, ")", 15>  <ParenDir, ")", 16>
```

---

### 2. Tratamento de erros léxicos (`ErroLexico`)

A exceção `ErroLexico` é levantada assim que um caractere inválido é encontrado.
Ela armazena a posição do erro e o caractere responsável, produzindo uma mensagem como:

```
Erro léxico na posição 4: caractere inesperado 'x' (ASCII 120)
```

O processo termina com código de saída `1`, separando a mensagem de erro para `stderr`
e a sequência de tokens para `stdout`, conforme boa prática de CLIs.

---

### 3. Analisador léxico (`AnalisadorLexico`)

A classe `AnalisadorLexico` mantém internamente um ponteiro de posição (`_pos`) sobre
a string de entrada. Duas interfaces públicas foram implementadas, conforme o enunciado
descreve as duas opções válidas:

- `proximo_token()` — retorna um token por vez; retorna `EOF` ao esgotar a entrada.
- `tokenizar()` — retorna todos os tokens em lista (sem EOF).

**Descarte de espaços em branco:** os quatro tipos citados no enunciado são ignorados —
espaço (`0x20`), tabulação (`0x09`), nova linha (`0x0A`) e retorno do carro (`0x0D`).

**Agrupamento de números:** ao encontrar um dígito, o lexer avança enquanto houver dígitos
consecutivos, reunindo todos em um único token `NUMERO` com o lexema completo.

**Caracteres simples:** parênteses e operadores são reconhecidos com lookup direto em dicionário,
resultando em O(1) por token.

---

### 4. Extensão opcional: comentários de linha (`#`)

O enunciado menciona explicitamente que os grupos podem adicionar suporte a comentários.
Foi implementado o comentário de linha iniciado por `#`: tudo da `#` até o fim da linha
(inclusive a ausência de `\n` no final do arquivo) é descartado silenciosamente.

Exemplo de uso:

```
# calcula (6 * 7)
(6 * 7)   # resultado: 42
```

---

### 5. Ponto de entrada (`main`)

O script aceita um argumento de linha de comando com o caminho do arquivo de entrada:

```bash
python lexer.py exemplos/valido1.ec1
```

Erros de arquivo não encontrado e erros léxicos são reportados no `stderr` com código de
saída `1`. A sequência de tokens vai para o `stdout`, facilitando redirecionamento e uso
em pipelines de testes.

---

### 6. Suite de testes (43 casos)

Todos os testes foram escritos com o módulo `unittest` da biblioteca padrão do Python,
sem dependências externas. Execução:

```bash
python tests/test_lexer.py
```

Resultado: **43 testes, 0 falhas.**

Distribuição por categoria:

| Categoria                     | Casos |
|-------------------------------|------:|
| Números (tipo, lexema, posição) |     5 |
| Operadores (`+`, `-`, `*`, `/`) |     4 |
| Parênteses                    |     3 |
| Expressões completas          |     6 |
| Espaços em branco             |     8 |
| Comentários (extensão `#`)    |     4 |
| Erros léxicos                 |     7 |
| Token EOF                     |     2 |
| Representação `str`           |     3 |
| **Total**                     |**43** |

Destaques:

- `test_exemplo_do_enunciado` verifica token por token (tipo, lexema **e** posição) contra o
  exemplo literal do enunciado, garantindo conformidade total.
- `test_posicao_com_espacos` verifica que as posições são do caractere de início do token na
  string original, não do token na sequência de tokens.
- Todos os testes de erro verificam não apenas que o `ErroLexico` é levantado, mas também
  que a **posição reportada** é a correta.

---

### 7. Arquivos de exemplo

Quatro arquivos `.ec1` foram criados em `exemplos/`:

| Arquivo         | Conteúdo                                      | Resultado esperado |
|-----------------|-----------------------------------------------|--------------------|
| `valido1.ec1`   | `(33 + (912 * 11))`                           | 9 tokens válidos   |
| `valido2.ec1`   | `((427 / 7) + (11 * (231 + 5)))`             | 17 tokens válidos  |
| `valido3.ec1`   | Expressão aninhada com comentário e indentação | 13 tokens válidos  |
| `invalido.ec1`  | `(12 x 5)`                                   | Erro léxico na posição 4 |

---

## Estrutura de arquivos entregue

```
ec1_lexer/
├── lexer.py              ← implementação principal
├── tests/
│   └── test_lexer.py     ← 43 testes automatizados
├── exemplos/
│   ├── valido1.ec1
│   ├── valido2.ec1
│   ├── valido3.ec1
│   └── invalido.ec1
├── README.md             ← instruções de uso e execução
├── PLANO.md              ← plano das próximas etapas
└── RELATORIO.md          ← este arquivo
```

---

## Decisões de projeto

**Por que `dataclass` para `Token`?**
Fornece `__eq__` automático por valor, o que permite comparações diretas nos testes
(`self.assertEqual(toks, esperado)`) sem código extra.

**Por que separar cada operador em tipo próprio em vez de um tipo genérico `OPERADOR`?**
O enunciado recomenda explicitamente esta abordagem para facilitar as etapas seguintes
do compilador (análise sintática e geração de código), que precisarão distinguir os operadores.

**Por que `frozenset` para `ESPACOS` e `dict` para `CHAR_SIMPLES`?**
Ambos oferecem lookup O(1). O `frozenset` deixa claro que o conjunto é imutável;
o `dict` mapeia diretamente do caractere para o tipo, eliminando um bloco de `if/elif`.

**Tratamento de erro: parar no primeiro erro vs. continuar.**
O enunciado apresenta as duas opções. Foi escolhida a abordagem de **parar no primeiro
erro**, que é mais simples de implementar e suficiente para esta etapa. A interface
`proximo_token()` levanta `ErroLexico` imediatamente, o que permite que um eventual
analisador sintático futuro decida como tratar a situação.
