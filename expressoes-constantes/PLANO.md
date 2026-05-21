# Plano de Desenvolvimento — Compilador EC1

**Universidade Federal da Paraíba (UFPB)**
**Centro de Informática - Curso de Ciência da Computação**
**Disciplina:** Construção de Compiladores 1
**Professor:** Andrei de Araújo Formiga
**Atividade:** 04 — Expressões Constantes 1  
**Linguagem alvo:** EC1 (Expressões Constantes 1)  
**Linguagem de implementação:** Python 3

---

## Visão geral

O objetivo final da série de atividades é construir um **compilador completo** para a linguagem EC1,
que traduz expressões aritméticas com operandos constantes para código assembly x86-64.
A Atividade 04 corresponde à **primeira etapa** desse processo: a análise léxica.

---

## Etapas planejadas

### Etapa 1 — Análise Léxica *(Atividade 04 — em andamento)*

**Objetivo:** transformar o texto bruto do programa EC1 em uma sequência de tokens classificados.

Tarefas:

1. Definir as **classes de tokens** da linguagem:
   - `Numero` — sequência de um ou mais dígitos
   - `ParenEsq` / `ParenDir` — parênteses `(` e `)`
   - `Soma`, `Sub`, `Mult`, `Div` — operadores aritméticos
   - `EOF` — marcador de fim de entrada

2. Definir a **estrutura de dados** do token com três campos:
   - `tipo` — a classe léxica
   - `lexema` — a string original que gerou o token
   - `posicao` — deslocamento (índice base 0) na string de entrada, para relatório de erros

3. Implementar o **`AnalisadorLexico`** com:
   - `proximo_token()` — retorna um token por vez
   - `tokenizar()` — retorna todos os tokens em lista
   - Descarte de espaços em branco (`' '`, `\t`, `\n`, `\r`)
   - Detecção e relato de **erros léxicos** com posição exata
   - *(Extensão opcional)* Suporte a comentários de linha com `#`

4. Implementar a **suite de testes** cobrindo:
   - Todos os tipos de token individuais
   - Expressões completas, incluindo o exemplo do enunciado
   - Variações de espaços em branco
   - Erros léxicos com verificação da posição reportada
   - Comentários (extensão)

5. Fornecer **arquivos de exemplo** e **documentação** de uso.

---

### Etapa 2 — Análise Sintática *(Atividade 05 — futura)*

**Objetivo:** verificar se a sequência de tokens forma um programa válido em EC1 e construir
a estrutura sintática (árvore de sintaxe abstrata — AST).

Tarefas previstas:

- Implementar um **parser descendente recursivo** baseado na gramática:
  ```
  <programa>  ::= <expressao>
  <expressao> ::= <literal>
                | '(' <expressao> <operador> <expressao> ')'
  <operador>  ::= '+' | '-' | '*' | '/'
  <literal>   ::= <digito>+
  ```
- Definir os **nós da AST**: `NodoNumero`, `NodoOperacao`
- Reportar **erros sintáticos** com posição via token inválido
- Reutilizar o analisador léxico da Etapa 1

---

### Etapa 3 — Interpretação / Avaliação *(Atividade futura)*

**Objetivo:** percorrer a AST e calcular o resultado da expressão em tempo de compilação.

Tarefas previstas:

- Implementar um **visitor/avaliador** da AST
- Tratar divisão por zero como erro semântico
- Produzir o valor inteiro resultante

---

### Etapa 4 — Geração de Código Assembly x86-64 *(Atividade futura)*

**Objetivo:** traduzir a AST para instruções assembly x86-64 funcionais.

Tarefas previstas:

- Gerar **prólogo e epílogo** da função `main` em assembly
- Traduzir operações para instruções `mov`, `add`, `sub`, `imul`, `idiv`
- Tratar a peculiaridade de `idiv` (uso de `rax`/`rdx`, sinal)
- Produzir um arquivo `.s` compilável com `gcc` ou `nasm`
- Testar com `gcc` e verificar o código de saída do processo

---

## Entregáveis por etapa

| Etapa | Arquivo(s) | Status |
|-------|-----------|--------|
| 1 — Léxico | `lexer.py`, `tests/test_lexer.py`, `README.md` | ✅ Concluído |
| 2 — Sintático | `parser.py`, `ast_nodes.py`, testes | 🔲 Planejado |
| 3 — Avaliador | `evaluator.py`, testes | 🔲 Planejado |
| 4 — Geração de código | `codegen.py`, testes de integração | 🔲 Planejado |

---

## Estrutura de diretório prevista ao final

```
ec1_compiler/
├── lexer.py          # Análise léxica
├── parser.py         # Análise sintática + AST
├── evaluator.py      # Avaliador da AST
├── codegen.py        # Geração de código x86-64
├── compiler.py       # Ponto de entrada principal
├── tests/
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_evaluator.py
│   └── test_codegen.py
├── exemplos/
│   ├── *.ec1         # Programas de exemplo
│   └── *.s           # Assembly gerado
└── README.md
```
