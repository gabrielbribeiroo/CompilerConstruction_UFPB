# Relatório de Implementação — Projeto Final: Compilador Fun estendido

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

### 1. Escolha de extensões

O enunciado do Projeto Final (seção 1) permite escolher **uma
extensão de complexidade média ou alta, ou pelo menos três extensões
simples** para acrescentar à linguagem Fun da Atividade 10. Optamos
por três extensões simples da seção 1.1:

1. Novos operadores de comparação: `<=`, `>=`, `!=`.
2. Operadores compostos de atribuição: `+=`, `-=`, `*=`, `/=`.
3. `return` como comando (retorno antecipado de dentro de `if`/`while`).

O critério foi manter o escopo contido e verificável dentro do prazo:
as três extensões são úteis de verdade (não apenas variações
sintáticas cosméticas), mas nenhuma delas exige um tipo novo ou muda a
representação de valores (tudo continua inteiro de 64 bits), o que
manteve o trabalho concentrado no lexer/parser/codegen sem tocar a
análise de tipos ou o modelo de memória.

### 2. Novos operadores de comparação (`lexer.py`, `codegen.py`)

`<=`, `>=` e `!=` são reconhecidos com o mesmo lookahead de 1
caractere já usado para `==` desde a Atividade 09: ao ler `<`, `>` ou
`!`, o lexer olha o caractere seguinte (sem avançar o cursor até
decidir) — se for `=`, consome os dois caracteres e produz o token
composto; senão, produz o token simples (`<`/`>`) ou levanta erro
léxico (`!` sozinho não existe em Fun, já que não há operador de
negação). A generalização ficou natural: em vez de tratar `<`, `>`,
`+`, `-`, `*`, `/` como casos avulsos em `CHAR_SIMPLES`, criamos um
único dicionário `_OPERADOR_COMPOSTO` mapeando cada caractere ao par
(token simples, token composto), com um único método
`_ler_operador_composto()` cobrindo os 6 operadores que agora têm
variante composta.

No codegen, `Op.MENOR_IGUAL`/`MAIOR_IGUAL`/`DIFERENTE` só precisaram
de três entradas novas em `_OP_COMPARACAO` (`setle`/`setge`/`setne`)
— o esquema `xor %rcx,%rcx; cmp %rbx,%rax; set<cc> %cl; mov %rcx,%rax`
já existente desde a Atividade 09 não mudou em nada.

### 3. Operadores compostos de atribuição (`parser.py`)

`x OP= exp` é implementado como **açúcar sintático puro**: o parser
desmonta a forma composta em `Atrib(x, OpBin(op, Var(x), exp))` no
próprio `_analisa_atrib()`, antes de a AST chegar à análise semântica
ou ao gerador de código. Não existe nenhum nó de AST novo para isso —
`x += 5;` produz exatamente a mesma árvore (e, por consequência, o
mesmo assembly) que `x = x + 5;` escrito por extenso. Essa decisão
eliminou qualquer necessidade de tocar `semantica.py` ou `codegen.py`
para esta extensão especificamente: toda a verificação de escopo e
toda a geração de código de `Atrib` já existiam e continuam servindo
sem alteração.

Um detalhe de posição: o `Var(x)` sintetizado dentro do `OpBin` usa a
mesma posição do identificador à esquerda, para que um erro semântico
de "variável usada antes de ser declarada" (se `x` não existir) aponte
para o lugar certo no código-fonte, e não para uma posição fictícia.

### 4. `return` como comando (`ast_fun.py`, `parser.py`, `semantica.py`, `codegen.py`)

Esta foi a extensão mais delicada, porque a gramática original de Fun
sempre termina o corpo de uma função/`main` com um `return`
**obrigatório**, fora da lista de comandos (`<cmd>* 'return' <exp>
';' '}'`). Permitir `return` **também** como comando comum, utilizável
dentro de `if`/`while`, sem tornar a gramática ambígua, exigiu uma
regra de desambiguação (detalhada em "Decisões de projeto").

**AST** (`ast_fun.py`): um nó novo, `Return(exp)`, e uma exceção
interna, `RetornoAntecipado(valor)`, usada por `_executar()` para
implementar a saída antecipada no interpretador de referência —
levantada ao encontrar um `Return`, ela se propaga naturalmente
através de qualquer aninhamento de `if`/`while` (a recursão Python já
faz esse trabalho) até ser capturada em `Chamada.avaliar()` ou
`Programa.avaliar()`, que a usam para decidir o valor de retorno em
vez de avaliar `exp_final`.

**Parser** (`parser.py`): `_analisa_corpo()` (novo método, reaproveitado
por `analisa_programa()` e `_analisa_fundecl()`, eliminando a
duplicação que existia entre as duas) reconhece `<cmd>* 'return' <exp>
';'` e resolve a ambiguidade olhando o token logo após o `;` de cada
`return`: se for `}`, é o obrigatório (vira `exp_final`, e o laço
para); caso contrário, é um retorno antecipado (vira um comando
`Return`, e o laço continua). Dentro de blocos aninhados (`if`/`while`,
via `_analisa_bloco_de_comandos()` → `_analisa_cmd()`), não há essa
ambiguidade: todo `return` ali é sempre um `Return` comum, já que um
bloco aninhado nunca tem "expressão final" própria.

**Semântica** (`semantica.py`): um caso novo em `_verifica_cmd()` para
`Return` — verifica a expressão com a mesma regra de escopo (local
antes de global) de qualquer outra expressão. Não insere nem exige
nada além disso.

**Codegen** (`codegen.py`): cada função (e o bloco `main`) ganha um
rótulo de saída fixo, emitido incondicionalmente logo após o código
da expressão final e antes do epílogo:

```
<nome>:
    push %rbp
    ...
    <codigo dos comandos, pode conter Return>
    <codigo da expressao final>
Lfim_<nome>:
    add $8*L, %rsp      # epilogo, igual a Atividade 10
    pop %rbp
    ret
```

Um `Return(exp)` gera o código de `exp` (deixando o valor em `%rax`,
a mesma convenção de sempre desde a Atividade 06) seguido de um `jmp
Lfim_<nome>` — pulando direto para o epílogo, sem executar o restante
dos comandos nem o código da expressão final. O bloco `main` segue a
mesma ideia com um rótulo fixo `Lfim_main`, emitido logo antes de
`call imprime_num`.

### 5. Variação sintática

Fora as três extensões escolhidas, seguimos exatamente a gramática da
Atividade 10 — nenhuma outra extensão simples da seção 1.1 (operadores
lógicos, strings, booleanos, funções primitivas) nem qualquer extensão
de complexidade média/alta foi implementada.

### 6. Suíte de testes (`tests/test_fun.py`)

**66 testes, 0 falhas**, em 8 classes — os 40 testes da Atividade 10
continuam passando sem nenhuma alteração (nenhuma regressão), mais 26
novos cobrindo as três extensões:

| Classe | Testes novos desta entrega |
| --- | ---: |
| `TestLexico` | 6 (comparações novas, atribuições compostas, operadores simples não afetados, `!=` bem-formado, `!` isolado é erro) |
| `TestParser` | 6 (comparações novas geram o `Op` certo, atribuição composta desmontada em `OpBin`, cada operador composto mapeado ao `Op` certo, `return` antecipado vira comando, `return` único continua não virando comando) |
| `TestErrosSintaticos` | 2 (corpo sem `return` final mesmo com antecipado presente, atribuição com operador inválido) |
| `TestSemantica` | 2 (variável não declarada dentro de `Return`, atribuição composta a variável não declarada) |
| `TestInterpretacao` | 5 (comparações novas, atribuição composta encadeada, `return` de dentro de `if`, de dentro de `while`, de dentro de recursão) |
| `TestEquivalenciaSemantica` | +13 programas na lista (antes 8, agora 21) |
| `TestCodegen` | 5 (SETcc novos, atribuição composta gera assembly idêntico à forma equivalente, rótulo de saída emitido para função e para `main`, `jmp` aponta para o rótulo certo) |
| `TestCLI` | 1 (compilação de um programa combinando as três extensões) |

Destaques:

- `test_atribuicao_composta_gera_mesmo_codigo_que_equivalente` prova,
  byte a byte, que o açúcar sintático da extensão 2 realmente não
  introduz nenhuma diferença no assembly gerado — o teste mais forte
  possível para essa decisão de design.
- `TestEquivalenciaSemantica` — já o teste mais importante da
  Atividade 10 — precisou apenas de 3 linhas novas no simulador
  (`setle`/`setge`/`setne`); o rótulo `Lfim_<nome>` é reconhecido pelo
  mesmo mecanismo genérico de rótulos que já existia (`_RE_LABEL_DEF`
  casa qualquer identificador seguido de `:`), sem exigir nenhuma
  mudança estrutural. Isso validou de ponta a ponta que um `return`
  antecipado dentro de `if`, de `while`, e mesmo dentro de uma chamada
  recursiva (`fibComReturn`), produz exatamente o mesmo resultado que
  o interpretador de referência.
- `test_corpo_sem_return_final_e_erro_mesmo_com_return_antecipado`
  confirma que a extensão 3 não afrouxou a exigência original de que
  todo corpo termine em `return` — ela só amplia onde mais `return`
  pode aparecer.

---

## Exemplo de saída — `classifica` (as três extensões combinadas)

Fonte (`exemplos/valido8_extensoes_combinadas.fun`):

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

Trecho do assembly gerado para `classifica`:

```
classifica:
    push %rbp
    mov %rsp, %rbp
    # if (n <= 0) {
    mov $0, %rax
    push %rax
    mov 16(%rbp), %rax
    pop %rbx
    xor %rcx, %rcx
    cmp %rbx, %rax
    setle %cl
    mov %rcx, %rax
    cmp $0, %rax
    jz Lfalso0
    # return 0; (retorno antecipado)
    mov $0, %rax
    jmp Lfim_classifica
    jmp Lfim0
Lfalso0:
    # } else {
Lfim0:
    # }
    # if (n >= 100) {
    ...
    setge %cl
    ...
    jz Lfalso1
    # return 2; (retorno antecipado)
    mov $2, %rax
    jmp Lfim_classifica
    jmp Lfim1
Lfalso1:
Lfim1:
    # return 1;
    mov $1, %rax
Lfim_classifica:
    pop %rbp
    ret
```

Executado, imprime `3` (`classifica(-5) = 0`, `classifica(50) = 1`,
`classifica(150) = 2`, somados via `+=`).

---

## Estrutura de arquivos entregue

```
projeto-final/
├── lexer.py
├── ast_fun.py
├── parser.py
├── semantica.py
├── codegen.py
├── compfun.py
├── runtime.s
├── exemplos/
│   ├── valido1.fun
│   ├── valido2.fun
│   ├── valido3.fun
│   ├── valido4.fun
│   ├── valido5_comparacoes.fun
│   ├── valido6_atribuicao_composta.fun
│   ├── valido7_return_antecipado.fun
│   ├── valido8_extensoes_combinadas.fun
│   ├── invalido_funcao_nao_declarada.fun
│   ├── invalido_numero_de_parametros.fun
│   └── invalido_variavel_fora_de_escopo.fun
├── tests/
│   └── test_fun.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

---

## Decisões de projeto

**Por que resolver a ambiguidade do `return` final olhando o token
após o `;`, em vez de restringir `return`-como-comando só a blocos
aninhados?**
A alternativa mais simples de implementar seria permitir `return`
apenas dentro de `if`/`while`, nunca diretamente no corpo de uma
função (evitando qualquer ambiguidade com o `return` final ali).
Rejeitamos essa alternativa porque ela criaria uma regra artificial e
surpreendente: por que `return` funcionaria dentro de um `if` mas não
diretamente no corpo? A regra de "olhar o que vem depois do `;`: se é
`}`, era o último; senão, é antecipado" é decidível com o lookahead de
1 token que o parser já usa em todo o resto da gramática, e generaliza
`return` da forma mais direta possível: ele é **sempre** um comando
válido em qualquer lugar onde um comando pode aparecer, e a única
regra especial é reconhecer quando ele coincide com o fim do corpo.

**Por que a atribuição composta é açúcar sintático no parser, em vez
de um nó de `Cmd` próprio (`AtribComposta`) com sua própria lógica de
avaliação e geração de código?**
Um `Atrib` já representa perfeitamente uma atribuição — a única
diferença de `x += e` para `x = e2` é *como* o valor a ser atribuído é
calculado, não *que tipo de comando* é. Desmontar no parser significa
que a análise semântica (que verifica se `x` está declarado) e a
geração de código (que emite o `mov` para `.bss` ou `deslocamento
(%rbp)`) não precisam saber que atribuição composta existe — elas
processam o `Atrib` resultante exatamente como sempre processaram.
Menos código, e a prova de corretude fica trivial:
`test_atribuicao_composta_gera_mesmo_codigo_que_equivalente` verifica
que o assembly é **idêntico** ao da forma equivalente escrita por
extenso.

**Por que o rótulo de saída (`Lfim_<nome>`) é sempre emitido, mesmo em
funções que não usam `return` antecipado?**
Emitir condicionalmente exigiria uma passada prévia pela AST da função
só para descobrir se ela contém algum `Return` em algum nível de
aninhamento — código extra para economizar uma única linha de rótulo
no `.s` gerado, que o GNU Assembler aceita sem nenhum aviso mesmo
quando não é alvo de nenhum `jmp`. Não vale a complexidade.

**Por que a extensão de comparações não precisou tocar
`semantica.py`?**
Porque `_verifica_exp()` trata `OpBin` genericamente — ela verifica os
dois operandos e devolve, sem nunca inspecionar *qual* operador
binário está sendo usado. Os três operadores novos são só mais valores
possíveis do `Enum Op`; nenhuma regra de escopo ou tipo depende de
qual comparação específica é usada.

---

## Dificuldades

A única dificuldade real desta entrega foi projetar a regra de
desambiguação do `return` como comando (descrita acima) sem
reestruturar a AST existente (`Programa`/`FunDecl` continuam com um
campo `exp_final` separado, exatamente como na Atividade 10) — a
alternativa de dobrar toda a gramática para "todo corpo é uma lista de
comandos, e o último **precisa** ser um `Return`" foi considerada, mas
descartada por exigir reescrever `semantica.py` e `codegen.py` para
validar essa nova invariante estruturalmente, em vez de reaproveitar o
mecanismo de `exp_final` já testado e funcionando. A solução adotada
(_analisa_corpo com peek de 1 token) resolve o mesmo problema com uma
mudança bem mais localizada, e o conjunto de testes (em especial
`test_corpo_sem_return_final_e_erro_mesmo_com_return_antecipado` e
`test_return_final_unico_nao_vira_comando`) dá confiança de que os
dois casos-limite (nenhum `return` antecipado; um `return` antecipado
seguido do final) continuam corretos.
