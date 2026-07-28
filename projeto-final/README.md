# Projeto Final — Compilador Fun estendido

Compilador completo para a linguagem **Fun** (Atividade 10) com três
extensões simples (seção 1.1 do enunciado do Projeto Final):

1. **Novos operadores de comparação**: `<=`, `>=`, `!=`.
2. **Operadores compostos de atribuição**: `+=`, `-=`, `*=`, `/=`.
3. **`return` como comando**: retorno antecipado de dentro de `if`/
   `while`, não só como a última instrução obrigatória do corpo.

A linguagem base (funções com parâmetros, variáveis locais, recursão
direta) é idêntica à da Atividade 10 — ver
[`compilador-fun/README.md`](../compilador-fun/README.md) para a
gramática completa e o "por que" das decisões de codegen herdadas
(convenção de chamada, frame pointer, etc). Este README cobre apenas
o que as três extensões mudam.

Exemplo (combinando as três extensões):

```
var contador = 0;

fun classifica(n) {
  if n <= 0 { return 0; } else {}
  if n >= 100 { return 2; } else {}
  return 1;
}

main {
  contador += classifica(0 - 5);
  contador += classifica(50);
  contador += classifica(150);
  return contador;
}
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
python compfun.py <arquivo.fun>
```

O compilador grava a saída no mesmo diretório da entrada, trocando a
extensão `.fun` por `.s`. Exemplo:

```sh
python compfun.py exemplos/valido8_extensoes_combinadas.fun
# gera exemplos/valido8_extensoes_combinadas.s
```

Em caso de erro léxico, sintático ou semântico, encerra com exit code
1, mensagem em `stderr` e nenhum `.s` é gravado.

## Montar e executar o `.s` gerado

```sh
python compfun.py exemplos/valido8_extensoes_combinadas.fun
as --64 -o exemplos/valido8_extensoes_combinadas.o exemplos/valido8_extensoes_combinadas.s
ld -o exemplos/valido8_extensoes_combinadas exemplos/valido8_extensoes_combinadas.o
./exemplos/valido8_extensoes_combinadas
# imprime: 3
```

## As três extensões em detalhe

### 1. Novos operadores de comparação (`<=`, `>=`, `!=`)

Reconhecidos pelo mesmo lookahead de 1 caractere já usado para `==`
desde a Atividade 09 (lê o caractere, olha o seguinte sem avançar até
decidir). Geram código idêntico ao de `<`/`>`/`==`, só trocando a
instrução `SETcc` usada (`setle`/`setge`/`setne` em vez de `setl`/
`setg`/`setz`) — o mesmo esquema `xor %rcx,%rcx; cmp %rbx,%rax;
set<cc> %cl; mov %rcx,%rax`.

```
main { return 5 <= 5; }   # -> 1
main { return 5 != 5; }   # -> 0
```

### 2. Operadores compostos de atribuição (`+=`, `-=`, `*=`, `/=`)

`x OP= exp` é **açúcar sintático**: o parser desmonta em `x = x OP
exp` no momento da análise sintática, antes de a AST chegar à análise
semântica ou ao codegen. Não há nó de AST novo, e o assembly gerado
para `x += 5;` é **byte a byte idêntico** ao de `x = x + 5;`.

```
var total = 10;
main {
  total += 5;   # total = total + 5
  total -= 2;   # total = total - 2
  total *= 3;   # total = total * 3
  total /= 3;   # total = total / 3
  return total; # -> 13
}
```

Como qualquer atribuição em Fun, `x` precisa já existir (variável
global ou local da função) — `y += 1;` com `y` não declarado é o
mesmo erro semântico de `y = y + 1;`.

### 3. `return` como comando

Antes desta extensão, o único jeito de "sair mais cedo" de uma função
era usar uma variável auxiliar para carregar o resultado até o fim do
corpo (como o `abs()` da Atividade 10 faz com `y`). Agora `return`
pode aparecer dentro de `if`/`while`, encerrando a função
imediatamente com aquele valor:

```
fun sinal(n) {
  if n < 0 { return 0 - 1; } else {}
  if n == 0 { return 0; } else {}
  return 1;
}
```

O corpo de uma função/main continua exigindo um `return` final
obrigatório (igual à Atividade 10) — a novidade é que `return` pode
*também* aparecer antes dele, em qualquer profundidade de
aninhamento. Ver [`RELATORIO.md`](RELATORIO.md) para como o parser
resolve essa ambiguidade sem mudar a gramática original.

## Estrutura

```
projeto-final/
├── lexer.py           # + 7 tokens: <=, >=, !=, +=, -=, *=, /=
├── ast_fun.py         # + Op.MENOR_IGUAL/MAIOR_IGUAL/DIFERENTE, Return, RetornoAntecipado
├── parser.py          # + op_atrib composto, return-como-comando (com desambiguacao)
├── semantica.py       # + verificacao de Return
├── codegen.py         # + setle/setge/setne, rotulo Lfim_<nome>/Lfim_main + jmp
├── compfun.py         # CLI: lex -> parse -> semantica -> codegen (inalterado)
├── runtime.s          # reusado sem alteracao (Atividade 02/06/07/08/09/10)
├── exemplos/
│   ├── valido1.fun .. valido4.fun          # herdados da Atividade 10 (sem extensoes)
│   ├── valido5_comparacoes.fun             # <=, >=
│   ├── valido6_atribuicao_composta.fun     # +=, -=, *=, /=
│   ├── valido7_return_antecipado.fun       # return dentro de if
│   ├── valido8_extensoes_combinadas.fun    # as tres extensoes juntas
│   ├── invalido_funcao_nao_declarada.fun   # herdados da Atividade 10
│   ├── invalido_numero_de_parametros.fun
│   └── invalido_variavel_fora_de_escopo.fun
├── tests/test_fun.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

## Testes

```sh
python tests/test_fun.py
```

66 testes em 8 classes: os 40 herdados da Atividade 10 (léxico,
parser, erros sintáticos, semântica, interpretação, equivalência
semântica, codegen, CLI) continuam passando sem alteração, mais 26
novos cobrindo as três extensões — incluindo um caso combinado nas
três extensões e retorno antecipado dentro de recursão e de `while`.

## Exemplos fornecidos

| Arquivo | Conteúdo | Resultado |
|---|---|---|
| `valido1.fun` .. `valido4.fun` | Exemplos da Atividade 10 (sem extensões) | `42`, `89`, `25`, `110` |
| `valido5_comparacoes.fun` | Classificação de idade com `<=`/`>=` | `2` |
| `valido6_atribuicao_composta.fun` | `+=`/`-=`/`*=`/`/=` encadeados | `13` |
| `valido7_return_antecipado.fun` | `sinal(n)` com `return` dentro de `if` | `-1` |
| `valido8_extensoes_combinadas.fun` | As três extensões juntas | `3` |
| `invalido_funcao_nao_declarada.fun` | Chamada a função nunca declarada | erro semântico, exit 1 |
| `invalido_numero_de_parametros.fun` | Aridade incorreta | erro semântico, exit 1 |
| `invalido_variavel_fora_de_escopo.fun` | Variável local usada fora da função | erro semântico, exit 1 |
