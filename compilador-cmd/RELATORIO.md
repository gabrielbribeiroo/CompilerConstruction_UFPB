# Relatório de Implementação — Atividade 09: Compilador Cmd (Comandos)

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

### 1. A linguagem Cmd: comandos e Turing-completude

Os compiladores das atividades anteriores traduziam apenas
**expressões** — sem capacidade de tomar decisões ou repetir código,
o que os deixava aquém de uma linguagem de programação de verdade.
Cmd estende EV (Atividade 08) com três comandos — condicional (`if`/
`else`), repetição (`while`) e atribuição — e três operadores de
comparação (`<`, `>`, `==`), tornando-a a primeira linguagem
**Turing-completa** deste conjunto de compiladores.

Um programa Cmd é `<decl>* '{' <cmd>* 'return' <exp> ';' '}'`: zero ou
mais declarações (iguais às de EV), seguidas de um corpo entre chaves
com zero ou mais comandos e uma expressão final obrigatória.
`return` não é um comando — só pode aparecer uma vez, ao final do
corpo do programa, nunca dentro de um `if` ou `while`. A linguagem não
tem tipo booleano separado: `0` é falso, qualquer outro valor é
verdadeiro — a mesma convenção usada nos flags do processador que a
geração de código explora diretamente.

### 2. Alterações léxicas (`lexer.py`)

Tokens novos: `CHAVE_ESQ`/`CHAVE_DIR` (`{`/`}`), `MENOR`/`MAIOR`/
`IGUAL_IGUAL` (`<`/`>`/`==`), e as palavras-chave `if`/`else`/`while`/
`return`.

Dois detalhes exigidos pela seção 3 do enunciado:

- **`==` vs `=`**: ao encontrar `=`, o lexer olha o caractere seguinte
  (sem avançar o cursor até decidir); se for outro `=`, o token é
  `IGUAL_IGUAL` (consumindo os dois caracteres); senão, é `IGUAL`
  (consumindo só um). Implementado em `_ler_igual()`.
- **Palavras-chave**: reconhecidas com a mesma regra léxica de
  identificador (`letra letra_digito*`) em `_ler_identificador_ou_palavra_chave()`;
  só depois de montar o lexema completo é que ele é comparado contra
  um dicionário fixo (`PALAVRAS_CHAVE`) para decidir se vira um token
  de palavra-chave ou um `IDENT` comum — exatamente a técnica sugerida
  no enunciado. Isso garante que `ifx` continue sendo um identificador
  válido, não confundido com a palavra-chave `if`.

### 3. Alterações na sintaxe (`parser.py`)

A análise do programa começa de forma similar a EV: zero ou mais
declarações (enquanto o próximo token for `IDENT`), terminadas por
`{`. Dentro do bloco, `_analisa_cmd()` decide por *peek* de 1 token
entre três alternativas — `if`/`while`/identificador — exatamente como
a seção 4 do enunciado descreve. A lista de comandos de qualquer
bloco (programa, ambos os braços do `if`, corpo do `while`) termina
quando o próximo token não é mais um desses três indicadores.

A análise de expressões ganha um nível de precedência novo, `exp`
(comparação), que fica **abaixo** de `exp_a` (aditivo) na gramática —
os operadores de comparação têm a precedência mais baixa da
linguagem. `_analisa_exp()` segue exatamente o mesmo formato de laço
já usado em `_analisa_exp_a()` e `_analisa_exp_m()` desde a Atividade
07, só trocando o conjunto de operadores e a função de nível inferior
chamada.

### 4. Árvore de sintaxe abstrata (`ast_cmd.py`)

Reaproveita `Exp`/`Const`/`Var`/`OpBin` das atividades anteriores.
`Op` ganha três valores para os operadores de comparação (`MENOR`,
`MAIOR`, `IGUAL`) — `OpBin.avaliar()` foi estendido com os três casos,
devolvendo `1`/`0`.

Novos nós de comando, todos `Cmd` (nova classe-base, análoga a `Exp`
mas para comandos):

- **`Atrib(nome, exp, posicao)`** — igual em espírito ao `Var.posicao`
  da Atividade 08: guarda a posição para mensagens de erro semântico
  sem afetar a igualdade estrutural (`field(compare=False)`).
- **`If(cond, cmds_then, cmds_else)`** — o braço `else` é obrigatório
  na gramática, mas `cmds_else` pode ser uma tupla vazia.
- **`While(cond, cmds)`**.
- **`Programa(declaracoes, comandos, exp_final)`** — ganhou o campo
  `comandos`.

`Programa.avaliar()` continua sendo o interpretador de referência.
Para executar os comandos, uma função livre `_executar(comandos, env)`
percorre a sequência mutando o ambiente: `Atrib` atualiza `env`
diretamente; `If` decide qual braço executar chamando `_executar`
recursivamente; `While` repete a chamada recursiva enquanto a
condição for verdadeira. Essa função serve como o "modelo de
execução" contra o qual validamos a geração de código.

### 5. Análise semântica (`semantica.py`)

Estende `verifica_programa()` da Atividade 08 com `_verifica_cmd()`,
que percorre recursivamente `If` (condição + os dois blocos) e
`While` (condição + o bloco). A verificação nova, exigida pela seção 5
do enunciado, é a de `Atrib`: um comando de atribuição tem dois
componentes a checar — a expressão do lado direito (não pode
referenciar variável não declarada) e a variável do lado esquerdo
(também precisa já estar declarada). Verificamos primeiro o lado
direito (ordem natural de execução: calcula-se o valor antes de
armazenar), depois o lado esquerdo. Como a atribuição não cria
variáveis novas, **nada é inserido na tabela de símbolos** ao
processar um `Atrib` — só `Decl` insere símbolos, exatamente como o
enunciado especifica.

### 6. Geração de código (`codegen.py`)

#### Comparações (seção 6.1 do enunciado)

Reaproveitamos o esquema de pilha já usado para `OpBin` aritmético
(`dir` primeiro, `push`, `esq`, `pop %rbx` → `%rax = esq`, `%rbx =
dir`). Esse esquema já deixa os operandos exatamente na ordem do
exemplo do enunciado para `A == B` (`%rax = A`, `%rbx = B`), então a
comparação foi encaixada sem nenhuma adaptação:

```
xor %rcx, %rcx
cmp %rbx, %rax
set<cc> %cl
mov %rcx, %rax
```

onde `set<cc>` é `setz` (`==`), `setl` (`<`) ou `setg` (`>`). `%rcx`
é usado como temporário porque `SETcc` só aceita um operando de 8
bits — não dá para usar `%rax` diretamente.

#### `if`/`else` e `while` (seção 6.2 do enunciado)

`GeradorDeCodigo` mantém um contador interno (`_contador_rotulos`)
incrementado a cada `if` ou `while` gerado, produzindo rótulos únicos
(`Lfalso0`/`Lfim0` para o primeiro `if`, `Linicio1`/`Lfim1` para o
próximo `while`, etc.). Os modelos de tradução seguem exatamente o
enunciado:

```
<codigo_E>
cmp $0, %rax
jz LfalsoN
<codigo_C1>
jmp LfimN
LfalsoN:
<codigo_C2>
LfimN:
```

```
LinicioN:
<codigo_E>
cmp $0, %rax
jz LfimN
<codigo_C>
jmp LinicioN
LfimN:
```

Também adicionamos comentários (`# if cond {`, `# } else {`, `# }`)
delimitando os blocos no `.s` gerado, na mesma linha da prática já
adotada na Atividade 08 para declarações/atribuições — útil para
conferir visualmente que a estrutura de rótulos e desvios está
correta.

#### Modelo de saída

Mesmo modelo com seções `.bss`/`.text` da Atividade 08. As variáveis
continuam vindo só das declarações (`_coleta_variaveis`, deduplicado);
o corpo agora inclui, em ordem: código das declarações, código dos
comandos (que pode conter `if`/`while` com seus próprios rótulos), e
por fim o código da expressão final.

### 7. Ponto de entrada (`compcmd.py`)

Mesma estrutura das atividades anteriores: lê o arquivo `.cmd` →
`analisar()` (léxico + sintático) → `verifica_programa()` (semântico)
→ `gerar_programa()` (codegen) → grava `.s`. Qualquer uma das três
exceções é capturada, imprime a mensagem em `stderr` e encerra com
exit code 1, sem gravar `.s`.

### 8. Variação sintática

Seguimos exatamente a sintaxe do enunciado, sem adotar nenhuma das
extensões da seção 7: operadores `<=`/`>=`, operadores booleanos
(`AND`/`OR`/`NOT`), comando de entrada, `if` sem `else`, ou atribuição
que cria variáveis novas — todas apresentadas explicitamente como
possibilidades opcionais, não como parte do artefato mínimo pedido na
seção 8.

### 9. Suíte de testes (`tests/test_cmd.py`)

**35 testes, 0 falhas**, em 7 classes:

| Classe | Foco | Casos |
| --- | --- | ---: |
| `TestLexico` | Tokens novos, `==` vs `=`, palavra-chave vs. identificador | 6 |
| `TestParser` | Estrutura da AST (`If`/`While`/`Atrib`, precedência da comparação) | 6 |
| `TestErrosSintaticos` | Entradas mal formadas (`if` sem `else`, bloco sem chaves, etc.) | 5 |
| `TestSemantica` | Atribuição a variável não declarada (ambos os lados, inclusive aninhada) | 5 |
| `TestInterpretacao` | `Programa.avaliar()` para os 4 exemplos do enunciado | 5 |
| `TestEquivalenciaSemantica` | Código gerado bate com o interpretador (10 programas, incluindo laços) | 1 |
| `TestCodegen` | Rótulos únicos por `if`/`while`, modelo completo | 3 |
| `TestCLI` | Comportamento de `compcmd.py` como subprocesso | 4 |
| **Total** | | **35** |

Destaques:

- `test_discriminante_do_enunciado`, `test_soma_do_enunciado`,
  `test_resto_da_divisao` e `test_mdc` reproduzem os **quatro
  exemplos do enunciado** (seções 2 e 9) e confirmam os valores
  citados: `8`, `45`, `2` e `6`, respectivamente.
- `TestEquivalenciaSemantica` é o teste mais importante desta
  atividade: o simulador de máquina de pilha das Atividades 06-08 foi
  estendido com um **program counter e um mapa de rótulos**, capaz de
  executar `jmp`/`jz` de verdade — inclusive **laços** (`while`), com
  um limite de passos (`MAX_PASSOS`) para detectar loop infinito por
  bug em vez de travar o teste. Isso prova que o código gerado para
  `if`/`while`/comparações é semanticamente equivalente ao
  interpretador, incluindo os quatro programas com `while` (soma,
  resto, mdc — que tem laços aninhados).
- `test_rotulos_unicos_para_ifs_diferentes` confirma que dois `if` no
  mesmo programa geram pares de rótulos distintos (`Lfalso0`/`Lfim0` e
  `Lfalso1`/`Lfim1`), evitando colisão de símbolos no assembly.

### 10. Arquivos de exemplo

Quatro programas válidos — os dois exemplos da seção 2 do enunciado
(discriminante e soma) e os dois exemplos adicionais da seção 9 (resto
da divisão e MDC, ambos usando `while` e o truque de `m + 1 > n` para
simular "maior ou igual", já que Cmd não tem esse operador) — e dois
inválidos: atribuição a uma variável nunca declarada, e atribuição
cuja expressão do lado direito referencia uma variável não declarada
dentro de um `if`.

---

## Exemplo de saída — discriminante (trecho)

```
# a = 1;
mov $1, %rax
mov %rax, a
...
# delta = ((b * b) - ((4 * a) * c));
...
# if (delta < 0) {
mov $0, %rax
push %rax
mov delta, %rax
pop %rbx
xor %rcx, %rcx
cmp %rbx, %rax
setl %cl
mov %rcx, %rax
cmp $0, %rax
jz Lfalso0
# delta = (0 - delta);
...
jmp Lfim0
Lfalso0:
# } else {
# delta = delta;
...
Lfim0:
# }
# return delta;
mov delta, %rax
call imprime_num
call sair
```

Executado, imprime `8` (delta calculado é `-8`, e o `if` inverte o
sinal porque `delta < 0`).

---

## Estrutura de arquivos entregue

```
compilador-cmd/
├── lexer.py
├── ast_cmd.py
├── parser.py
├── semantica.py
├── codegen.py
├── compcmd.py
├── runtime.s
├── exemplos/
│   ├── valido1.cmd
│   ├── valido2.cmd
│   ├── valido3.cmd
│   ├── valido4.cmd
│   ├── invalido_atrib_var_nao_declarada.cmd
│   └── invalido_atrib_direita_nao_declarada.cmd
├── tests/
│   └── test_cmd.py
├── README.md
├── PLANO.md
└── RELATORIO.md
```

---

## Decisões de projeto

**Por que os operandos da comparação já saem na ordem certa do
esquema de pilha existente?**
Porque o esquema de pilha das atividades anteriores (`dir` primeiro,
`push`, `esq`, `pop %rbx`) sempre deixa `%rax = esq` e `%rbx = dir`
depois do `pop`. O exemplo do enunciado para `A == B` assume
exatamente essa disposição (`%rax = A`, `%rbx = B`) antes do `cmp`.
Não precisamos adaptar nada — a mesma técnica de tradução usada para
`+`/`-`/`*`/`/` desde a Atividade 06 já resolve comparações de graça.

**Por que usar um contador de instância (`_contador_rotulos`) em vez
de nomes de rótulo determinados pela posição do `if`/`while` na
árvore?**
É a técnica sugerida literalmente pelo enunciado ("manter um contador
de quantos rótulos foram gerados até agora") e é a mais simples que
garante unicidade sem exigir nenhuma análise adicional da árvore
(como profundidade de aninhamento ou um caminho único por nó). Cada
`if`/`while`, não importa o quão aninhado, recebe um número novo.

**Por que o simulador de teste precisa de um *program counter*
explícito, e não apenas percorrer as linhas em ordem?**
Porque agora o código gerado tem **desvios de verdade** (`jmp`/`jz`)
que podem andar para trás no texto (voltar para `Linicio0:` em um
`while`), o que o simulador linear das atividades anteriores (que só
executava de cima para baixo) não suportava. Construímos um mapa
`rotulo → índice` e um laço com `pc` que só avança sequencialmente
quando a instrução não é um desvio — exatamente como um processador
de verdade interpretaria o mesmo código.

**Por que checar o lado direito da atribuição antes do lado
esquerdo na análise semântica?**
Reflete a ordem natural de execução do comando: primeiro se calcula o
valor da expressão, só depois ele é armazenado na variável. O
enunciado não impõe uma ordem específica entre as duas checagens
(ambas resultam em erro, de qualquer forma), mas essa ordem é a mais
intuitiva e é a que usamos consistentemente.

**Por que os comentários de bloco (`# if cond {`, `# } else {`,
`# }`) no código gerado?**
Mesma justificativa da Atividade 08: custo desprezível, e tornam o
`.s` muito mais fácil de inspecionar visualmente — foi assim que
confirmamos rapidamente, durante o desenvolvimento, que a estrutura de
rótulos de um `if` dentro de outro `if` estava correta antes mesmo de
rodar os testes automatizados.

---

## Dificuldades

Nenhuma dificuldade significativa. O enunciado é bastante explícito
sobre os modelos de tradução de comparações, `if` e `while` (inclusive
com o assembly completo de exemplo), o que tornou a implementação do
codegen bem direta. Os pontos que exigiram mais atenção:

- **Escrever o simulador de teste com desvios reais.** Diferente das
  atividades anteriores, onde o "simulador" era apenas um interpretador
  linear de cima para baixo, aqui foi necessário simular um *program
  counter* de verdade, com salto para trás (loop) e um limite de
  passos de segurança para não travar a suíte de testes em caso de bug
  que gerasse um loop infinito de verdade.
- **Diferenciar `==` de `=` no lexer.** Resolvido com um lookahead
  explícito de 1 caractere antes de decidir o tipo do token, sem
  consumir o segundo `=` a menos que ele realmente esteja lá.
- **Garantir que `ifx` não vire a palavra-chave `if`.** A regra de
  reconhecer o identificador inteiro primeiro e só depois comparar
  contra a tabela de palavras-chave resolve isso automaticamente, mas
  foi importante escrever um teste específico para confirmar.
