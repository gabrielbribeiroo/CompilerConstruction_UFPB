# Relatório - Atividade 04 - Expressões Constantes 1 - Análise Léxica

**Universidade Federal da Paraíba (UFPB)**
**Centro de Informática - Curso de Ciência da Computação**
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

# Analisador Léxico EC1

Implementação em Python do analisador léxico para a linguagem **EC1 (Expressões Constantes 1)**.

## Requisitos

- Python 3.7 ou superior (sem dependências externas)

## Estrutura do projeto

```
ec1_lexer/
├── lexer.py              # Analisador léxico
├── tests/
│   └── test_lexer.py     # Suite de testes (43 casos)
├── exemplos/
│   ├── valido1.ec1       # Expressão simples
│   ├── valido2.ec1       # Expressão aninhada
│   ├── valido3.ec1       # Múltiplos espaços / linhas
│   └── invalido.ec1      # Exemplo com erro léxico
└── README.md
```

## Como executar o analisador léxico

```bash
python lexer.py <arquivo_de_entrada>
```

### Exemplos

```bash
python lexer.py exemplos/valido1.ec1
python lexer.py exemplos/valido2.ec1
python lexer.py exemplos/valido3.ec1
```

Saída esperada para `(33 + (912 * 11))`:

```
<ParenEsq, "(", 0>
<Numero, "33", 1>
<Soma, "+", 4>
<ParenEsq, "(", 6>
<Numero, "912", 7>
<Mult, "*", 11>
<Numero, "11", 13>
<ParenDir, ")", 15>
<ParenDir, ")", 16>
```

### Erro léxico

```bash
python lexer.py exemplos/invalido.ec1
```

Saída (no stderr):

```
Erro léxico na posição 4: caractere inesperado 'x' (ASCII 120)
```

O processo termina com código de saída `1` em caso de erro léxico.

## Como executar os testes

```bash
python tests/test_lexer.py
```

Ou com saída verbosa:

```bash
python -m unittest tests.test_lexer -v
```

### Cobertura dos testes

|Categoria             |Casos |
|----------------------|-----:|
|Números               |5     |
|Operadores            |4     |
|Parênteses            |3     |
|Expressões completas  |6     |
|Espaços em branco     |8     |
|Comentários (opcional)|4     |
|Erros léxicos         |7     |
|Token EOF             |2     |
|Representação (str)   |3     |
|**Total**             |**43**|

## Classes léxicas

|Tipo      |Lexema                                 |
|----------|---------------------------------------|
|`Numero`  |sequência de dígitos decimais (`0`–`9`)|
|`ParenEsq`|`(`                                    |
|`ParenDir`|`)`                                    |
|`Soma`    |`+`                                    |
|`Sub`     |`-`                                    |
|`Mult`    |`*`                                    |
|`Div`     |`/`                                    |
|`EOF`     |— (sinaliza fim da entrada)            |

## Extensão: comentários

O analisador suporta comentários de linha iniciados por `#` (ignorados até o fim da linha):

```
# calcula (6*7)
(6 * 7)
```

## Uso da API em Python

```python
from lexer import AnalisadorLexico, TipoToken

lexer = AnalisadorLexico("(3 + 4)")
tokens = lexer.tokenizar()          # lista de todos os tokens
for tok in tokens:
    print(tok)

# ou token a token:
lexer2 = AnalisadorLexico("42")
tok = lexer2.proximo_token()        # Token(NUMERO, "42", 0)
eof = lexer2.proximo_token()        # Token(EOF, "", 2)
```