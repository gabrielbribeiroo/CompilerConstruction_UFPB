# Relatório de Implementação — Atividade 06: Compilador EC1

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

### 1. Reaproveitamento das atividades anteriores

- **`lexer.py`** — análise léxica idêntica à entregue na Atividade 04.
- **`ast_ec1.py`** — hierarquia de classes da AST (Atividade 05): `Exp`
  abstrata, `Const`, `OpBin` (`dataclass(frozen=True)`), enum `Op`.
- **`parser.py`** — analisador sintático descendente recursivo da
  Atividade 05, com a exceção `ErroSintatico` que carrega posição e
  mensagem clara.
- **`runtime.s`** — exatamente o `runtime.s` fornecido pelo professor na
  Atividade 02 (`imprime_num`, `sair`). Necessário para o `.s` gerado
  poder ser montado e linkado em um executável.

### 2. Gerador de código (`codegen.py`)

A classe `GeradorDeCodigo` percorre recursivamente a AST e emite assembly
x86-64 (sintaxe GNU Assembler). Para cada tipo de nó:

- **`Const(n)`** → uma única instrução `mov $n, %rax`.
- **`OpBin(op, esq, dir)`** → segue o esquema baseado na pilha descrito na
  seção 4.1 do enunciado, na **opção 2 (ordem invertida)** da página 9:
  1. Emite código de `dir` (deixa o resultado em `%rax`).
  2. `push %rax`.
  3. Emite código de `esq` (sobrescreve `%rax` com o operando esquerdo).
  4. `pop %rbx` (operando direito sai da pilha para `%rbx`).
  5. Emite a instrução da operação, sempre na forma `<instr> %rbx, %rax`,
     produzindo o resultado em `%rax`.

Mapeamento dos operadores:

| `Op`   | Instrução emitida |
| ------ | ----------------- |
| `SOMA` | `add %rbx, %rax`  |
| `SUB`  | `sub %rbx, %rax`  |
| `MULT` | `imul %rbx, %rax` |
| `DIV`  | `cqo` + `idiv %rbx` |

A divisão precisa do `cqo` antes do `idiv` porque a instrução `idiv` em
x86-64 divide o par `rdx:rax` pelo operando — `cqo` estende o sinal de
`%rax` para preencher `%rdx`, garantindo divisão inteira com sinal
corretamente. O quociente fica em `%rax`.

A escolha pela opção 2 (ordem invertida) é deliberada: depois do `pop`,
`%rax` tem o operando esquerdo e `%rbx` o direito, exatamente a ordem
natural de operandos para `sub` e `idiv`. Não é preciso nenhum truque
extra para corrigir a ordem em operadores não-comutativos.

`GeradorDeCodigo` expõe duas APIs:

- `gerar(arvore)` — devolve só o código da expressão.
- `gerar_programa(arvore)` — devolve o `.s` completo, com o modelo de
  saída em volta (seção `.text`, rótulo `_start`, chamadas finais a
  `imprime_num` e `sair`, `.include "runtime.s"`), idêntico ao da
  Atividade 02.

### 3. Ponto de entrada (`compec1.py`)

Recebe o nome do arquivo `.ec1` na linha de comando, executa
**lex → parse → codegen** e grava a saída em um arquivo `.s` ao lado da
entrada (trocando a extensão). Erros léxicos, sintáticos ou de E/S vão
para `stderr` com exit code 1; nesses casos nenhum `.s` é gravado.

A escolha de gravar em arquivo (em vez de imprimir em `stdout`) segue a
preferência expressa na seção 6 do enunciado.

### 4. Suíte de testes (`tests/test_codegen.py`)

**15 testes, 0 falhas**, divididos em 6 classes do `unittest`:

| Classe | Foco | Casos |
| --- | --- | ---: |
| `TestCodigoDeConstantes` | `Const(n)` produz a instrução `mov` correta | 3 |
| `TestCodigoDeOperacoes` | Código literal exato para cada um dos 4 operadores | 4 |
| `TestAninhamento` | Pilha balanceada em expressão aninhada à direita | 1 |
| `TestEquivalenciaSemantica` | Semântica do código gerado bate com o interpretador | 2 |
| `TestProgramaCompleto` | `gerar_programa()` envolve o código no modelo correto | 2 |
| `TestCLI` | Comportamento de `compec1.py` como subprocesso | 3 |

Destaque para a classe `TestEquivalenciaSemantica`: ela contém um
**simulador minimalista da máquina de pilha** (~30 linhas em Python) que
interpreta exatamente as instruções que o nosso codegen pode emitir
(`mov $n, %rax`, `push %rax`, `pop %rbx`, `add/sub/imul %rbx, %rax`,
`cqo`, `idiv %rbx`). Para cada um dos 16 programas de teste — incluindo
os dois exemplos do enunciado e vários casos com operadores
não-comutativos aninhados em ambas as ordens — o simulador executa o
código gerado e o resultado é comparado com o `avaliar()` do
interpretador da Atividade 05. Se os dois batem para todos os programas,
o código gerado é semanticamente correto, mesmo sem precisar montar e
linkar o `.s` na máquina onde os testes rodam.

A classe `TestCLI` invoca `compec1.py` via `subprocess` e verifica
comportamento de ponta a ponta: entrada válida produz `.s` correto;
entrada com erro de sintaxe sai com código 1 e não cria `.s`; arquivo
inexistente é reportado de forma adequada.

### 5. Arquivos de exemplo

Seis programas válidos em `exemplos/`, cobrindo: constante simples
(`333`), multiplicação simples (`(6 * 7)`), os dois exemplos do enunciado
(`(33 + (912 * 11))` e `((427 / 7) + (11 * (231 + 5)))`), subtração para
estressar não-comutatividade (`(11 - 7)`), e soma aninhada à direita
(`(7 + (3 + 8))`).

---

## Exemplo de saída — `(33 + (912 * 11))`

```
#
# Saida gerada pelo compilador EC1
#
    .section .text
    .globl _start

_start:
    mov $11, %rax
    push %rax
    mov $912, %rax
    pop %rbx
    imul %rbx, %rax
    push %rax
    mov $33, %rax
    pop %rbx
    add %rbx, %rax
    call imprime_num
    call sair

    .include "runtime.s"
```

Trace: a multiplicação interna `(912 * 11)` é executada primeiro;
`imul` deixa `10032` em `%rax`. Esse valor é empilhado, `33` vai para
`%rax`, `pop` traz `10032` para `%rbx`, e `add` produz `10065` em `%rax`,
que é então passado para `imprime_num`.

---

## Estrutura de arquivos entregue

```
compilador-ec1/
├── lexer.py
├── ast_ec1.py
├── parser.py
├── codegen.py
├── compec1.py
├── runtime.s
├── exemplos/
│   ├── valido1.ec1
│   ├── valido2.ec1
│   ├── valido3.ec1
│   ├── valido4.ec1
│   ├── valido5.ec1
│   └── valido6.ec1
├── tests/
│   └── test_codegen.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

---

## Decisões de projeto

**Por que a opção 2 (ordem invertida) em vez da opção 1?**
A opção 1 (página 8) emite o operando esquerdo primeiro, empilha, depois
o direito, e termina com `pop %rbx`. Para soma e multiplicação,
comutativas, funciona direto. Para subtração e divisão, exige um
truque: trocar `pop %rbx` por `mov %rax, %rbx` + `pop %rax`. A opção 2
não precisa desse caso especial — a ordem natural já fica `rax = esq`,
`rbx = dir`, que é a forma que `sub` e `idiv` esperam. Código mais
uniforme.

**Por que `imul %rbx, %rax` (forma de dois operandos) em vez de `imul %rbx`?**
A forma de dois operandos é mais segura: faz `rax = rax * rbx` sem
mexer em `%rdx`. A forma de um operando faz `rdx:rax = rax * rbx`,
sobrescrevendo `%rdx`, o que não causa problema neste compilador mas é
desnecessário.

**Por que `cqo` + `idiv` em vez de só `div`?**
`idiv` é divisão com sinal, coerente com a tipagem inteira da AST e com
o `avaliar()` que usa `int(a / b)` (truncamento para zero, exatamente o
que `idiv` faz). `cqo` estende o sinal de `%rax` em `%rdx`, o que é
indispensável antes de qualquer `idiv` — sem isso, `%rdx` carregaria
lixo da operação anterior.

**Por que o codegen como classe em vez de funções soltas?**
A classe acumula o resultado em `self._linhas`, o que evita passar e
juntar listas em cada chamada recursiva. A interface continua simples
(duas funções de conveniência `gerar_codigo` e `gerar_programa`
embrulham a criação da instância para uso comum).

**Equivalência semântica como teste principal.**
A forma mais sólida de validar o codegen seria montar e executar os
`.s` em uma máquina x86-64 Linux. Como nem todos os ambientes de
desenvolvimento têm essa toolchain disponível, escrevemos um
simulador da máquina de pilha em Python que interpreta exatamente o
subconjunto de instruções que o codegen pode emitir. Para qualquer
programa EC1 válido, simulador e `avaliar()` do interpretador
produzem o mesmo número — o que prova, no teste, que o código
gerado tem a mesma semântica do interpretador. Mantemos também a
possibilidade de validar manualmente um `.s` no Linux (descrito no
README).

**Itens NÃO implementados (intencionalmente).**
A seção 7 do enunciado discute otimização: alocação inteligente de
registradores para usar menos pilha, e propagação de constantes (toda
expressão EC1 é constante, então o compilador poderia, em teoria,
calcular o valor em tempo de compilação e emitir apenas `mov $V, %rax`).
A seção 7 apresenta isso como **o que ficou de fora**, não como o que
deve ser entregue — assim como a seção 6 não pede isso. Não foi
implementado.

---

## Dificuldades

Nenhuma dificuldade significativa. O esquema descrito na seção 4 do
enunciado é direto. Os pontos que exigiram atenção foram:

- **Decidir entre as duas opções de ordem** (operando esquerdo primeiro
  vs. direito primeiro). Optamos pela opção 2 por simplicidade — vide
  decisão acima.
- **Divisão com sinal correto.** Inicialmente esquecemos o `cqo`; o
  teste de equivalência semântica imediatamente apontou divergência
  para os programas que envolviam divisão, e o ajuste foi trivial.
- **Indentação consistente no template completo.** O código que sai
  do codegen é cru (sem indentação), mas o template do `.s` indenta
  cada instrução com 4 espaços. `gerar_programa` faz essa
  reindentação antes de embrulhar no modelo.
