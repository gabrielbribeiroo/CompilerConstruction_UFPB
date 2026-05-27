# Analisador Sintatico + Interpretador EC1

Implementacao da Atividade 05 da disciplina de Construcao de Compiladores 1.

A entrada e um programa na linguagem **EC1** (Expressoes Constantes 1) — uma
expressao aritmetica com constantes inteiras e parenteses explicitos em cada
operacao. A saida e o valor numerico do programa, obtido por interpretacao
da arvore sintatica produzida pelo analisador.

Gramatica:

```
<programa>  ::= <expressao>
<expressao> ::= <literal> | '(' <expressao> <operador> <expressao> ')'
<operador>  ::= '+' | '-' | '*' | '/'
<literal>   ::= <digito>+
```

## Requisitos

- Python 3.8 ou superior. Nao ha dependencias externas.

## Como executar

A partir desta pasta:

```sh
python ec1.py <arquivo.ec1>
```

O programa imprime o valor da expressao em `stdout`. Em caso de erro lexico,
sintatico, de E/S ou divisao por zero, imprime mensagem em `stderr` e termina
com codigo de saida 1.

Exemplos:

```sh
$ python ec1.py exemplos/valido1.ec1
333

$ python ec1.py exemplos/valido3.ec1
10065

$ python ec1.py exemplos/invalido_parenteses.ec1
Erro sintatico na posicao 17: esperado ParenDir, encontrado fim da entrada
$ echo $?
1
```

## Estrutura

```
analise-sintatica-ec1/
├── lexer.py          # analise lexica (Token, TipoToken, AnalisadorLexico)
├── ast_ec1.py        # arvore: Exp (abstrata), Const, OpBin, enum Op
├── parser.py         # AnalisadorSintatico (descendente recursivo) + ErroSintatico
├── ec1.py            # ponto de entrada da linha de comando
├── exemplos/         # quatro programas validos e tres com erro
├── tests/
│   └── test_parser.py
├── README.md
├── PLANO.md          # plano de implementacao
└── RELATORIO.md      # relatorio entregue ao professor
```

## Testes

```sh
python tests/test_parser.py
```

A bateria possui 34 casos divididos em quatro classes:

- `TestArvoreSintatica` — verifica a AST produzida (estrutura literal).
- `TestInterpretador` — verifica que `avaliar()` produz o valor correto.
- `TestErrosSintaticos` — verifica deteccao de programas mal formados.
- `TestImpressaoCanonica` — verifica que `__str__` na AST reconstitui a
  expressao no formato esperado.

## Exemplos fornecidos

| Arquivo                          | Conteudo                                   | Resultado esperado          |
|----------------------------------|--------------------------------------------|-----------------------------|
| `valido1.ec1`                    | `333`                                      | `333`                       |
| `valido2.ec1`                    | `(6 * 7)`                                  | `42`                        |
| `valido3.ec1`                    | `(33 + (912 * 11))`                        | `10065`                     |
| `valido4.ec1`                    | `((427 / 7) + (11 * (231 + 5)))`           | `2657`                      |
| `invalido_parenteses.ec1`        | `(33 + (912 * 11)` (faltando `)`)          | erro sintatico, exit 1      |
| `invalido_operador.ec1`          | `(3 3 4)` (esperava operador)              | erro sintatico, exit 1      |
| `invalido_lixo_no_fim.ec1`       | `(6 * 7) 42` (token extra apos a raiz)     | erro sintatico, exit 1      |
