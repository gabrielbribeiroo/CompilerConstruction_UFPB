# Compilador EC2 (Atividade 07)

Compilador completo para a linguagem **EC2**, que estende a EC1
(Atividades 04–06) permitindo escrever expressões aritméticas com o
**mínimo de parênteses**, seguindo as regras usuais de:

- **Precedência**: `*` e `/` são calculados antes de `+` e `-`.
- **Associatividade à esquerda**: em uma cadeia de operadores de mesma
  precedência, a ordem é da esquerda para a direita — `10 - 8 - 2`
  significa `(10 - 8) - 2`, não `10 - (8 - 2)`.

Parênteses continuam funcionando normalmente para forçar uma ordem
diferente da padrão.

Gramática:

```
<exp_a> ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m> ::= <prim>  (('*' | '/') <prim>)*
<prim>  ::= <num> | '(' <exp_a> ')'
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
python compec2.py <arquivo.ec2>
```

O compilador grava a saída no mesmo diretório da entrada, trocando a
extensão `.ec2` por `.s`. Exemplo:

```sh
python compec2.py exemplos/valido1.ec2
# gera exemplos/valido1.s
```

Em caso de erro léxico ou sintático, encerra com exit code 1, mensagem
em `stderr` e nenhum `.s` é gravado.

## Montar e executar o `.s` gerado

```sh
python compec2.py exemplos/valido1.ec2
as --64 -o exemplos/valido1.o exemplos/valido1.s
ld -o exemplos/valido1 exemplos/valido1.o
./exemplos/valido1
# imprime: 22   (7 + 5 * 3, NAO 36)
```

## Estrutura

```
compilador-ec2/
├── lexer.py           # reusado sem alteração (Atividade 04/05/06)
├── ast_ec1.py         # reusado sem alteração (Atividade 05/06)
├── parser.py          # NOVO: exp_a / exp_m / prim (precedência + associatividade)
├── codegen.py         # reusado sem alteração (Atividade 06)
├── compec2.py         # CLI principal
├── runtime.s          # reusado sem alteração (Atividade 02/06)
├── exemplos/
│   ├── valido1.ec2   # 7 + 5 * 3                  -> 22
│   ├── valido2.ec2   # (7 + 5) * 3                -> 36
│   ├── valido3.ec2   # 10 - 8 - 2                 -> 0
│   ├── valido4.ec2   # 100 / 10 / 2               -> 5
│   ├── valido5.ec2   # 2 + 3 * 4 - 10 / 5         -> 12
│   ├── valido6.ec2   # (33 + (912 * 11))          -> 10065 (compat. EC1)
│   └── invalido1.ec2 # 7 + * 3 — erro sintático
├── tests/test_parser_precedencia.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

## O que muda em relação à Atividade 06

Só o **analisador sintático**. A análise léxica, a árvore de sintaxe
abstrata e o gerador de código são exatamente os mesmos arquivos da
Atividade 06 (verificados byte a byte idênticos). O parser agora reconhece
três não-terminais em vez de um só:

| Não-terminal | Papel | Chama |
|---|---|---|
| `exp_a` | Nível aditivo (`+`, `-`), precedência mais baixa | `exp_m` |
| `exp_m` | Nível multiplicativo (`*`, `/`), precedência mais alta | `prim` |
| `prim`  | Constante ou `( exp_a )` | `exp_a` (recursivo via parênteses) |

Cada não-terminal com repetição (`(...)* `) vira um laço que usa
`olhar_proximo()` (peek) para decidir se continua sem consumir um token
que não pertence a essa produção; a cada iteração o nó binário recém
criado vira o novo operando esquerdo, o que produz associatividade à
esquerda diretamente, sem pós-processamento.

## Testes

```sh
python tests/test_parser_precedencia.py
```

26 testes em 6 classes, cobrindo precedência, associatividade (soma,
subtração, multiplicação, divisão), compatibilidade retroativa com
programas EC1 (parênteses obrigatórios), erros sintáticos, equivalência
semântica entre o código gerado e o interpretador (reaproveitando o
simulador de máquina de pilha da Atividade 06), e o comportamento do
CLI via subprocess.

## Exemplos fornecidos

| Arquivo | Conteúdo | Resultado |
|---|---|---|
| `valido1.ec2` | `7 + 5 * 3` | `22` |
| `valido2.ec2` | `(7 + 5) * 3` | `36` |
| `valido3.ec2` | `10 - 8 - 2` | `0` |
| `valido4.ec2` | `100 / 10 / 2` | `5` |
| `valido5.ec2` | `2 + 3 * 4 - 10 / 5` | `12` |
| `valido6.ec2` | `(33 + (912 * 11))` | `10065` |
| `invalido1.ec2` | `7 + * 3` | erro sintático, exit 1 |
