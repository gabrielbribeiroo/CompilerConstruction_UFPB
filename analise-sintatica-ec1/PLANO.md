# Plano de Implementação — Atividade 05

**Objetivo:** estender o trabalho da Atividade 04 para incluir análise sintática
da linguagem EC1 (Expressões Constantes 1), gerando uma árvore de sintaxe
abstrata (AST) e usando essa árvore para interpretar o programa.

## Gramática alvo (do enunciado)

```
<programa>  ::= <expressao>
<expressao> ::= <literal> | '(' <expressao> <operador> <expressao> ')'
<operador>  ::= '+' | '-' | '*' | '/'
<literal>   ::= <digito>+
```

## Estratégia

1. **Análise descendente recursiva** com uma função por não-terminal —
   `analisa_exp()` e `analisa_operador()`. O método é o sugerido no enunciado
   (seções 3 e 6).
2. **Decisão por lookahead de 1 token** — `analisa_exp()` consome o próximo
   token e decide pela regra `<literal>` ou pela regra `'(' ... ')'` em função
   do tipo desse token.
3. **AST com hierarquia de classes** (`Exp` abstrata, `Const`, `OpBin`),
   conforme proposto na seção 5 do enunciado. O operador é representado por
   uma enumeração `Op` com os quatro valores possíveis.
4. **Interpretação por varredura da árvore** implementada como um método
   `avaliar()` na classe base `Exp`, sobrescrito em `Const` e `OpBin` —
   conforme sugerido na seção 8 do enunciado.
5. **Erros sintáticos** são reportados via exceção `ErroSintatico`, com
   posição (índice do token na entrada) e mensagem descrevendo o que se
   esperava versus o que foi encontrado. O processo encerra com código de
   saída diferente de zero e mensagem em `stderr`.

## Estrutura dos arquivos

```
analise-sintatica-ec1/
├── lexer.py          # análise léxica (reusada/adaptada da Atividade 04)
├── ast_ec1.py        # Exp (abstract), Const, OpBin, Op (enum)
├── parser.py         # AnalisadorSintatico + ErroSintatico
├── ec1.py            # ponto de entrada: lê arquivo, lex → parse → avalia
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
├── PLANO.md          # este arquivo
└── RELATORIO.md
```

## Interface entre lexer e parser

O lexer expõe duas formas, conforme discutido na seção 7 do enunciado:

- `proximo_token()` — retorna o próximo token e avança o cursor;
- `olhar_proximo()` — *peek* sem consumir.

O parser usa principalmente `proximo_token()` (consumindo) e, no final,
verifica se o próximo token é `EOF` para garantir que não há lixo após a
expressão.

## Testes planejados

A bateria de testes deve cobrir, pelo menos:

- Constantes inteiras simples (1 dígito, vários dígitos).
- Operações binárias com cada um dos quatro operadores.
- Expressões aninhadas (vários níveis de profundidade).
- O exemplo literal do enunciado: `(33 + (912 * 11))` deve produzir uma
  AST específica e avaliar para `10065`.
- Erros sintáticos: parêntese não fechado, operador inválido, parêntese
  fechando inesperado, conteúdo após a expressão raiz, entrada vazia.
- Reconstituição da string original via `__str__()` da AST.

## Itens deliberadamente NÃO implementados

O enunciado menciona como possibilidades adicionais (seção 9) a impressão
da árvore em formato ASCII visual e em formato graphviz. Essas extensões
não fazem parte do que o enunciado pede para entregar e não serão
implementadas, conforme orientação de manter o escopo no estritamente
solicitado.

A impressão textual simples (reconstrução de `(esq op dir)`) é mencionada
no enunciado como *útil para testes* e será implementada — sem custo
adicional — via `__str__()` nos nós da AST.

## Validação

A entrega é considerada pronta quando:

- `python ec1.py exemplos/valido1.ec1` imprime o valor avaliado correto
  para os quatro arquivos de exemplo válidos.
- `python ec1.py exemplos/invalido_*.ec1` imprime uma mensagem clara de
  erro sintático no `stderr` e termina com código de saída 1.
- `python tests/test_parser.py` roda toda a suíte sem falhas.
