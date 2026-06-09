# Roteiro do Vídeo — Marco 1 (Compilador EC1)

**Disciplina:** Construção de Compiladores 1
**Marco 1:** compilador completo para a linguagem **EC1** (Expressões Constantes 1)
**Duração-alvo:** ~7:30 (margem para 5–10 min)

## Divisão por integrante

| Integrante              | Bloco                                                      | Tempo  | Slides   |
|-------------------------|------------------------------------------------------------|--------|----------|
| **Davi**                | Introdução, contexto, visão geral do compilador            | ~1:00  | 1–3      |
| **Nathan**              | Atividade 04 — Análise Léxica                              | ~2:00  | 4–6      |
| **João Vitor**          | Atividade 05 — Análise Sintática + Interpretador           | ~2:00  | 7–10     |
| **Gabriel**             | Atividade 06 — Geração de Código + Demo                    | ~2:30  | 11–14    |
| (qualquer um)           | Encerramento                                               | ~0:15  | 15       |

## Dicas gerais de gravação

- Cada integrante grava seu trecho separadamente, mostrando a webcam em um canto da tela enquanto os slides ocupam o resto. Depois o vídeo final é só concatenar os clipes.
- Ao mostrar código no slide, **falar o que ele faz**, não ler linha por linha.
- A demo do Gabriel vale mais que qualquer slide — investir tempo aí.
- Se a gravação ficar muito longa, o que dá pra cortar primeiro: detalhes de testes (mencionar números, não enumerar classes), e o slide de visão geral (Davi pode resumir oral).

---

## Slide 1 — Capa
**Quem fala:** Davi
**Tempo:** ~0:15

> "Olá, professor. Somos o grupo formado por Davi, Gabriel, João Vitor e Nathan, e nesta apresentação vamos mostrar como construímos o compilador para a linguagem EC1, percorrendo as atividades 04, 05 e 06."

**Na tela:** slide com título, integrantes, disciplina, professor.

---

## Slide 2 — A linguagem EC1
**Quem fala:** Davi
**Tempo:** ~0:25

> "EC1, ou Expressões Constantes 1, é uma linguagem mínima de expressões aritméticas com constantes inteiras e parênteses obrigatórios em cada operação. A gramática tem três produções: um programa é uma expressão; uma expressão é um literal inteiro ou uma operação binária entre parênteses; e o operador é um dos quatro aritméticos. Como cada operação é parentizada, não tem precedência pra resolver."

**Na tela:** gramática BNF e dois exemplos: `333` e `(33 + (912 * 11))`.

---

## Slide 3 — Visão geral do compilador
**Quem fala:** Davi
**Tempo:** ~0:20

> "O compilador segue o pipeline clássico: o **lexer** transforma a string fonte em uma sequência de tokens; o **parser** monta uma árvore de sintaxe abstrata a partir dos tokens; o **gerador de código** percorre a árvore e produz assembly x86-64 pronto para ser montado e linkado. Cada uma dessas etapas foi entregue em uma atividade — Nathan agora vai falar do lexer."

**Na tela:** diagrama horizontal: `código fonte → [lexer] → tokens → [parser] → AST → [codegen] → .s`.

---

## Slide 4 — Atividade 04: Análise Léxica
**Quem fala:** Nathan
**Tempo:** ~0:25

> "Na atividade 04 implementamos o analisador léxico. O trabalho dele é varrer a string de entrada caractere por caractere e agrupar em tokens — números viram um único token com o lexema completo, parênteses e operadores viram tokens individuais, e espaços em branco são descartados."

**Na tela:** lista de `TipoToken` (NUMERO, PAREN_ESQ, PAREN_DIR, SOMA, SUB, MULT, DIV, EOF).

---

## Slide 5 — Estrutura do Token e API do lexer
**Quem fala:** Nathan
**Tempo:** ~0:45

> "Cada token guarda três coisas: o tipo, o lexema original e a posição no arquivo — essa posição é o que permite mensagens de erro com 'caractere inesperado na posição N'. A classe `AnalisadorLexico` expõe duas interfaces que o enunciado sugere: `proximo_token` que consome um token por vez, e `olhar_proximo` que faz peek sem avançar. As duas usam um cursor interno e um buffer de um token só."

**Na tela:** trecho do `Token` (dataclass) + assinatura das duas funções.

---

## Slide 6 — Saída para o exemplo do enunciado
**Quem fala:** Nathan
**Tempo:** ~0:50

> "Pra dar uma ideia concreta: a entrada `(33 + (912 * 11))` produz nove tokens, todos com a posição correta do caractere original — não a posição na sequência, o que é uma diferença sutil mas importante pra debug. Nossos testes — 43 casos no unittest — verificam exatamente isso, incluindo posições, erros léxicos com posição correta, e a extensão opcional de comentários iniciados por `#` que decidimos implementar. Agora o João Vitor vai mostrar como esses tokens viram uma árvore."

**Na tela:** entrada `(33 + (912 * 11))` em cima, e a sequência de tokens em formato `<Tipo, "lexema", pos>` embaixo.

---

## Slide 7 — Atividade 05: Análise Sintática
**Quem fala:** João Vitor
**Tempo:** ~0:30

> "Na atividade 05 usamos os tokens do lexer para construir uma árvore sintática. Implementamos um analisador descendente recursivo, que é o jeito mais simples e direto de escrever um parser à mão: uma função pra cada não-terminal da gramática."

**Na tela:** a gramática EC1 (de novo, agora com cores destacando os não-terminais que viram funções).

---

## Slide 8 — Parser descendente recursivo
**Quem fala:** João Vitor
**Tempo:** ~0:50

> "A função `_analisa_exp` consome o próximo token e ramifica pelo tipo: se for um número, devolve um nó `Const`; se for um parêntese abrindo, chama recursivamente para o operando esquerdo, depois lê o operador, depois recursivamente o direito, e exige o parêntese fechando. A função `analisa_programa` chama `_analisa_exp` e garante que o próximo token é EOF — isso pega entradas como `(6 * 7) 42` que teriam lixo depois da expressão raiz."

**Na tela:** pseudocódigo de `_analisa_exp` (versão limpa, sem detalhes de erro).

---

## Slide 9 — A árvore de sintaxe abstrata
**Quem fala:** João Vitor
**Tempo:** ~0:25

> "A árvore tem três classes: `Exp` abstrata, `Const` para folhas com um inteiro, e `OpBin` para nós internos com operador e dois filhos. Usamos `dataclass(frozen=True)` para ganhar igualdade por valor de graça — o que tornou os testes do parser triviais de escrever."

**Na tela:** as três classes em Python (resumidas) + a árvore desenhada de `(33 + (912 * 11))`.

---

## Slide 10 — Interpretador (tree-walking)
**Quem fala:** João Vitor
**Tempo:** ~0:30

> "Para confirmar que a árvore captura a expressão certa, implementamos também um interpretador: cada classe da árvore tem um método `avaliar`. `Const.avaliar` devolve o valor; `OpBin.avaliar` chama recursivamente nos filhos e aplica o operador. Pra `(33 + (912 * 11))`, sai `10065`. Esse interpretador depois vai servir como gabarito para validar o gerador de código. Gabriel."

**Na tela:** método `avaliar` de `OpBin` + linha de comando: `python ec1.py exemplos/valido3.ec1 → 10065`.

---

## Slide 11 — Atividade 06: o problema da geração de código
**Quem fala:** Gabriel
**Tempo:** ~0:30

> "Na atividade 06, juntamos lexer e parser com o gerador de código e fechamos o compilador. O problema central da geração é: como traduzir uma operação binária pra assembly sem perder o resultado do operando esquerdo enquanto se calcula o direito? O enunciado mostra que usar um registrador extra não escala — uma expressão com N operadores poderia precisar de N registradores no pior caso."

**Na tela:** o exemplo problemático do enunciado: `(7 + (3 + 8))` quebra se RBX é reusado.

---

## Slide 12 — Esquema da pilha (opção 2 do enunciado)
**Quem fala:** Gabriel
**Tempo:** ~0:50

> "A solução é a pilha. Usamos a opção 2 da seção 4.1: para `(A op B)`, geramos primeiro o código de B — resultado em RAX —, fazemos `push %rax`; depois o código de A — também acaba em RAX —; depois `pop %rbx`, que coloca B em RBX e deixa A em RAX. Aí a operação `<instr> %rbx, %rax` produz `A op B` em RAX. A vantagem dessa ordem invertida é que ela já deixa os operandos na posição natural para `sub` e `idiv`, sem precisar de truque pra corrigir a ordem."

**Na tela:** os 5 passos do esquema + tabela dos quatro operadores (`add`, `sub`, `imul`, `cqo+idiv`).

---

## Slide 13 — Demo: programa → assembly
**Quem fala:** Gabriel
**Tempo:** ~0:50

> "Vou mostrar funcionando. Compilando `(33 + (912 * 11))`: o gerador percorre a árvore e produz esse assembly aqui — repara que ele compila a multiplicação primeiro, empilha 10032, depois carrega 33, faz pop pra trazer 10032 pra RBX, e soma, deixando 10065 em RAX. Esse arquivo `.s` é completo: tem `.section .text`, o rótulo `_start`, e no final chama `imprime_num` e `sair`."

**Na tela:** terminal mostrando `python compec1.py exemplos/valido3.ec1` + o conteúdo do `.s` gerado, com os comentários `# multiplica`, `# empilha`, etc, destacados.

---

## Slide 14 — Testes do compilador completo
**Quem fala:** Gabriel
**Tempo:** ~0:30

> "A validação tem 15 testes em 6 classes. O mais importante é o teste de equivalência semântica: escrevemos um simulador da máquina de pilha em Python — uns 30 linhas — que entende exatamente as instruções que o codegen emite, e pra 16 programas EC1 ele tem que produzir o mesmo número que o interpretador da atividade 05 produzir. Se os dois batem em todos, o gerador é semanticamente correto, mesmo sem precisar montar e rodar o `.s` na máquina onde os testes rodam."

**Na tela:** saída de `python tests/test_codegen.py` mostrando `Ran 15 tests in 0.X s — OK`.

---

## Slide 15 — Encerramento
**Quem fala:** (qualquer um, sugerimos Gabriel)
**Tempo:** ~0:15

> "Com isso fechamos o Marco 1: temos um compilador EC1 completo, do código-fonte ao assembly executável. O repositório com os três projetos e todos os testes está na descrição. Obrigado!"

**Na tela:** link do repo + nomes dos integrantes.

---

## Checklist final de gravação

- [ ] Cada integrante gravou seu trecho
- [ ] Os slides estão na ordem certa e sem typo
- [ ] A demo do Gabriel foi feita ao vivo (não captura de tela estática)
- [ ] O áudio está audível em todos os trechos
- [ ] Duração total entre 5 e 10 minutos
- [ ] Arquivo final em formato compatível com a plataforma de entrega
