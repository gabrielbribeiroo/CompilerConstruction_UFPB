# Plano de Implementação — Projeto Final

**Objetivo:** estender o compilador Fun (Atividade 10) com extensões
escolhidas pelo grupo, conforme a seção 1 do enunciado do Projeto Final.

## Extensões escolhidas

O enunciado exige **uma extensão de complexidade média ou alta, ou
pelo menos três extensões simples**. Optamos por três extensões
simples (seção 1.1 do enunciado):

1. **Novos operadores de comparação**: `<=` (menor-ou-igual), `>=`
   (maior-ou-igual), `!=` (diferente).
2. **Operadores compostos de atribuição**: `+=`, `-=`, `*=`, `/=`.
3. **`return` como comando**: possibilidade de retornar de uma função
   a partir de qualquer ponto do seu corpo (inclusive de dentro de
   `if`/`while`), não apenas como a última instrução obrigatória.

Critério de escolha: as três são extensões genuinamente úteis (não
apenas exercícios sintáticos) que não exigem nenhum tipo novo nem
mudança na representação de valores (tudo continua sendo inteiro de
64 bits) — mantendo o escopo contido e testável dentro do prazo,
seguindo a mesma régua de "fazer o simples, bem feito" adotada nas
atividades anteriores.

## O que muda em cada estágio

| Estágio | Mudança |
|---|---|
| `lexer.py` | 7 tokens novos: `<=`, `>=`, `!=`, `+=`, `-=`, `*=`, `/=`. Reconhecidos com o mesmo lookahead de 1 caractere já usado para `==` desde a Atividade 09. `!` isolado (sem `=` em seguida) é erro léxico — não existe operador de negação em Fun. |
| `ast_fun.py` | `Op` ganha `MENOR_IGUAL`, `MAIOR_IGUAL`, `DIFERENTE`. Novo nó de comando `Return(exp)`. Nova exceção interna `RetornoAntecipado`, usada por `_executar`/`Chamada.avaliar`/`Programa.avaliar` para implementar a saída antecipada. **Nenhum nó novo para atribuição composta** — é açúcar sintático desmontado no parser. |
| `parser.py` | Reconhece os 3 operadores de comparação novos em `_analisa_exp`; `_analisa_atrib` aceita `=`/`+=`/`-=`/`*=`/`/=` e desmonta a forma composta em `Atrib(x, OpBin(op, Var(x), exp))`; `return` passa a ser reconhecível também como comando comum dentro de blocos aninhados, com uma regra de desambiguação para o `return` final obrigatório (ver seção abaixo). |
| `semantica.py` | Um caso novo em `_verifica_cmd` para `Return` (mesma regra de escopo de qualquer expressão). Nenhuma mudança em `_verifica_exp` — comparações novas são só mais valores de `Op`, tratados genericamente. |
| `codegen.py` | 3 entradas novas em `_OP_COMPARACAO` (`setle`/`setge`/`setne`). Cada função (e o bloco `main`) ganha um rótulo de saída fixo (`Lfim_<nome>`/`Lfim_main`), emitido logo após o código da expressão final; um `Return` gera o código da sua expressão seguido de `jmp` direto para esse rótulo. |

## Desambiguação de `return` como comando

A gramática original de Fun sempre termina o corpo de uma função/main
com um `return` **obrigatório**, fora da lista de comandos:

```
<corpo> ::= <cmd>* 'return' <exp> ';' '}'
```

Permitir `return` **também** como comando comum (usável dentro de
`if`/`while`) sem tornar a gramática ambígua exige uma regra: ao
encontrar um `return` no nível direto do corpo de uma função/main, o
parser olha o token logo após o `;` que o encerra:

- se for `}`, este `return` é o obrigatório (encerra o corpo, vira
  `exp_final`, exatamente como antes);
- caso contrário, é um retorno antecipado (vira um comando `Return`,
  e o parser continua reconhecendo comandos).

Dentro de blocos **aninhados** (corpo de `if`/`while`), não há essa
ambiguidade: todo `return` ali é sempre um comando `Return` comum, já
que um bloco aninhado nunca tem uma "expressão final" própria.

## Geração de código de `Return`

Cada função ganha um rótulo de saída fixo, emitido incondicionalmente
logo após o código da expressão final (e antes do epílogo):

```
<nome>:
    push %rbp
    ...
    <codigo dos comandos, pode conter Return>
    <codigo da expressao final>
Lfim_<nome>:
    <epilogo: add $8*L,%rsp / pop %rbp / ret>
```

Um `Return(exp)` gera `<codigo de exp>` (deixando o valor em `%rax`,
a mesma convenção de sempre) seguido de `jmp Lfim_<nome>` — pulando
direto para o epílogo, sem executar o restante dos comandos nem o
código da expressão final. O bloco `main` segue a mesma ideia, com um
rótulo fixo `Lfim_main` logo antes de `call imprime_num`.

Quando uma função não usa `return` antecipado, o rótulo simplesmente
não é alvo de nenhum `jmp` — o GNU Assembler aceita rótulos não
referenciados sem nenhum aviso, então não há necessidade de gerá-lo
condicionalmente.

## Testes planejados

Reaproveitamos a suíte completa da Atividade 10 (66 testes, incluindo
o simulador de equivalência semântica que modela `%rsp`/`%rbp` como
endereços reais) e acrescentamos, por extensão:

- **Léxico**: os 7 tokens compostos novos, os operadores simples
  continuando intactos quando não seguidos de `=`, e o erro léxico de
  `!` isolado.
- **Sintático**: comparações novas geram o `Op` certo; atribuição
  composta desmonta em exatamente o mesmo `Atrib`/`OpBin` que a forma
  equivalente escrita por extenso; `return` antecipado dentro de `if`
  vira um comando `Return` (não afeta o `exp_final`); um corpo sem
  `return` final é erro sintático mesmo com um `return` antecipado
  presente.
- **Semântico**: uma variável não declarada usada dentro de um
  `return` antecipado é rejeitada, assim como numa atribuição
  composta.
- **Interpretação**: um caso por extensão, mais uma combinação das
  três em um único programa (`classifica`), mais retorno antecipado
  dentro de recursão e dentro de `while`.
- **Equivalência semântica**: o simulador ganha `setle`/`setge`/
  `setne`; a lista de programas testados cresce com um caso por
  extensão e o caso combinado — o rótulo `Lfim_<nome>` é reconhecido
  pelo mesmo mecanismo genérico de rótulos já existente, sem exigir
  nenhuma mudança estrutural no simulador além dos 3 `SETcc` novos.
- **Codegen**: `setle`/`setge`/`setne` presentes; atribuição composta
  gera exatamente o mesmo assembly que a forma equivalente; o rótulo
  de saída é emitido e o `jmp` de um retorno antecipado aponta para
  ele.
- **CLI**: compilação de um programa que combina as três extensões.

## Itens deliberadamente fora de escopo

- Qualquer extensão de complexidade média/alta (tipos novos, arrays,
  otimização, etc.) — o grupo optou pelo caminho de três extensões
  simples, per a seção 1 do enunciado.
- Operadores lógicos/booleanos (E, OU, NÃO) e strings/booleanos como
  tipo — extensões simples adicionais listadas no enunciado, mas não
  escolhidas por este grupo.
- Funções primitivas de impressão e funções matemáticas pré-definidas
  — idem.

## Validação

- `python tests/test_fun.py` roda toda a suíte (66 testes) sem falhas.
- `python compfun.py exemplos/valido8_extensoes_combinadas.fun` gera
  `.s` que, montado e executado, produz o valor esperado (`3`).
