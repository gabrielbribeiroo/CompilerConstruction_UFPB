# Roteiro do Vídeo — Projeto Final (Compilador Fun estendido)

**Disciplina:** Construção de Compiladores 1
**Projeto Final:** três extensões simples sobre a linguagem Fun (Atividade 10)
**Duração-alvo:** ~7:00 (margem para 5–10 min)

## Divisão por integrante

| Integrante              | Bloco                                                        | Tempo  | Slides   |
|--------------------------|---------------------------------------------------------------|--------|----------|
| **Davi**                | Introdução + o que mudou desde o Marco 1                     | ~1:15  | 1–3      |
| **Nathan**               | Extensão 1 (comparações) + Extensão 2 (atribuição composta)  | ~1:45  | 4–6      |
| **João Vitor**           | Extensão 3 — return como comando                              | ~1:45  | 7–9      |
| **Gabriel**              | Demo combinando as três + testes                              | ~1:45  | 10–12    |
| (qualquer um)            | Encerramento                                                  | ~0:15  | 13       |

## Dicas gerais de gravação

- Mesmo esquema do Marco 1: cada integrante grava seu trecho separadamente, webcam num canto, slides ocupando o resto.
- Como o Projeto Final é sobre **mudanças pontuais** em cima de um compilador que já existia, evitar reexplicar tudo o que já foi apresentado no Marco 1 — o Slide 2 é justamente um resumo de 20 segundos disso, não uma nova aula.
- A demo do Gabriel (slide 10) vale mais que os slides de decisão de projeto — investir tempo aí.
- Se precisar cortar tempo: o slide de "o que mudou desde o Marco 1" pode ser dito de cabeça em vez de lido, e os detalhes de contagem de testes podem virar só "66 testes, todos passando".

---

## Slide 1 — Capa
**Quem fala:** Davi
**Tempo:** ~0:15

> "Olá, professor. Somos o grupo formado por Davi, Gabriel, João Vitor e Nathan, e nesta apresentação vamos mostrar o Projeto Final: três extensões que implementamos em cima do compilador Fun da Atividade 10."

**Na tela:** slide com título, integrantes, disciplina, professor.

---

## Slide 2 — O que mudou desde o Marco 1
**Quem fala:** Davi
**Tempo:** ~0:35

> "Desde o Marco 1, que cobriu até a Atividade 06 com o compilador EC1, o grupo entregou mais quatro atividades: a 07 trouxe precedência de operadores, tirando a obrigação de parentizar tudo; a 08 introduziu variáveis e a primeira análise semântica de verdade, com tabela de símbolos; a 09 acrescentou condicionais, laços e comparações, tornando a linguagem Turing-completa; e a 10 acrescentou funções — parâmetros, variáveis locais e recursão, com uma convenção de chamada baseada em pilha. O Projeto Final parte exatamente daí."

**Na tela:** linha do tempo horizontal: EC1 (06) → EC2 (07) → EV (08) → Cmd (09) → Fun (10) → Projeto Final.

---

## Slide 3 — A linguagem Fun, rapidamente
**Quem fala:** Davi
**Tempo:** ~0:25

> "Fun é a linguagem da Atividade 10: funções com parâmetros, variáveis locais próprias e recursão direta, geradas com uma convenção de chamada em pilha e RBP como frame pointer. O objetivo do Projeto Final é escolher extensões — nós escolhemos três extensões simples, listadas na seção 1.1 do enunciado — e implementá-las mantendo toda a base de Fun funcionando sem regressão."

**Na tela:** exemplo curto de Fun (`abs`/`fib`) + as três extensões escolhidas listadas: comparações novas, atribuição composta, `return` como comando.

---

## Slide 4 — Extensão 1: novos operadores de comparação
**Quem fala:** Nathan
**Tempo:** ~0:40

> "A primeira extensão acrescenta `<=`, `>=` e `!=`. No lexer, isso é só mais um lookahead de 1 caractere — a mesma técnica já usada para `==` desde a Atividade 09: ao ler `<`, `>` ou `!`, o lexer olha o caractere seguinte, e só consome o `=` se ele realmente estiver lá. `!` sozinho não existe em Fun, então vira erro léxico. No gerador de código, cada operador novo é só mais uma instrução `SETcc` — `setle`, `setge`, `setne` — reaproveitando o mesmo esquema de comparação que já existia."

**Na tela:** trecho do lexer (`_ler_operador_composto`) + tabela dos 6 operadores com variante composta.

---

## Slide 5 — Extensão 2: atribuição composta
**Quem fala:** Nathan
**Tempo:** ~0:45

> "A segunda extensão acrescenta `+=`, `-=`, `*=` e `/=`. A decisão de projeto mais importante aqui foi não criar nenhum nó de árvore novo: `x += 5` é desmontado, ainda no parser, em exatamente a mesma árvore que `x = x + 5` escrito por extenso. Isso significa que a análise semântica e o gerador de código não precisam saber que atribuição composta existe — e um teste garante que o assembly gerado pelas duas formas é byte a byte idêntico."

**Na tela:** `x += 5;` ao lado de `x = x + 5;`, com uma seta mostrando que os dois viram o mesmo `Atrib(OpBin(...))`.

---

## Slide 6 — Por que açúcar sintático, e não um nó novo?
**Quem fala:** Nathan
**Tempo:** ~0:20

> "A pergunta que a gente se fez foi: vale a pena criar um `AtribComposta` com sua própria lógica de verificação e geração de código? A resposta foi não — um `Atrib` já representa perfeitamente uma atribuição, a única diferença é como o valor é calculado. Menos código, e a prova de corretude fica trivial de escrever."

**Na tela:** citação da seção "Decisões de projeto" do RELATORIO.md (resumida).

---

## Slide 7 — Extensão 3: o problema do `return` como comando
**Quem fala:** João Vitor
**Tempo:** ~0:40

> "A terceira extensão foi a mais delicada: permitir `return` dentro de um `if` ou `while`, não só como a última instrução obrigatória do corpo. O problema é que a gramática original de Fun sempre termina o corpo de uma função com um `return` obrigatório, fora da lista de comandos. Se a gente simplesmente deixasse `return` aparecer em qualquer lugar, o parser não saberia mais dizer qual `return` é o final e qual é antecipado."

**Na tela:** a gramática original de Fun com o `return` obrigatório destacado, e a pergunta "qual é o do meio, e qual é o do fim?".

---

## Slide 8 — A solução: peek de 1 token
**Quem fala:** João Vitor
**Tempo:** ~0:40

> "A solução foi olhar o token logo depois do `;` de cada `return`: se for `}`, é o obrigatório, encerra o corpo. Se não for, é um retorno antecipado, vira um comando comum, e o parser continua. Dentro de um `if` ou `while` não existe essa ambiguidade — lá, todo `return` é sempre antecipado, porque um bloco aninhado nunca tem uma expressão final própria."

**Na tela:** pseudocódigo de `_analisa_corpo()` (a decisão do peek) + o exemplo `sinal(n)` usando `return` dentro de dois `if`s.

---

## Slide 9 — Geração de código do `return` antecipado
**Quem fala:** João Vitor
**Tempo:** ~0:35

> "No gerador de código, cada função — e o bloco `main` — ganha um rótulo de saída fixo, `Lfim_<nome>`, logo antes do epílogo. Um `return` antecipado só calcula sua expressão e dá um `jmp` direto pra esse rótulo, pulando o resto dos comandos. Quando a função não usa retorno antecipado, o rótulo simplesmente não vira alvo de nenhum `jmp` — o assembler aceita de boa."

**Na tela:** trecho de assembly de `classifica` mostrando `jmp Lfim_classifica` e o rótulo antes do epílogo.

---

## Slide 10 — Demo: as três extensões juntas
**Quem fala:** Gabriel
**Tempo:** ~0:50

> "Vou mostrar as três funcionando juntas. Esse programa classifica um número em três faixas usando `<=` e `>=`, sai antecipadamente de cada `if` com `return`, e acumula o resultado com `+=`. Compilando, o gerador produz esse assembly — repara no `setle`, no `jmp Lfim_classifica`, e no fato de que `contador += classifica(...)` gera exatamente o mesmo código que `contador = contador + classifica(...)` geraria."

**Na tela:** terminal com `python compfun.py exemplos/valido8_extensoes_combinadas.fun` + trecho do `.s` gerado, destacando `setle`, `jmp Lfim_classifica` e a limpeza de pilha do `+=`.

---

## Slide 11 — Testes
**Quem fala:** Gabriel
**Tempo:** ~0:35

> "A suíte inteira da Atividade 10 continua passando sem nenhuma alteração — 40 testes, zero regressão — e acrescentamos 26 testes novos, total de 66. O destaque continua sendo o simulador de equivalência semântica: ele já tinha pego dois bugs reais durante a Atividade 10, e aqui só precisou de três linhas novas — `setle`, `setge`, `setne` — pra validar as três extensões contra o interpretador de referência, incluindo `return` antecipado dentro de recursão."

**Na tela:** saída de `python tests/test_fun.py` mostrando `Ran 66 tests ... OK`.

---

## Slide 12 — Escopo e o que ficou de fora
**Quem fala:** Gabriel
**Tempo:** ~0:20

> "O enunciado pedia uma extensão média/alta ou pelo menos três simples — escolhemos o caminho de três simples, mantendo o escopo controlado: nenhuma delas exige tipo novo, então a análise de tipos e o modelo de memória não mudaram em nada."

**Na tela:** lista das extensões NÃO escolhidas (operadores lógicos, strings, booleanos, etc.) riscada, ao lado das três escolhidas.

---

## Slide 13 — Encerramento
**Quem fala:** (qualquer um, sugerimos Davi)
**Tempo:** ~0:15

> "Com isso fechamos o Projeto Final: comparações novas, atribuição composta e `return` como comando, tudo em cima do compilador Fun que construímos desde a Atividade 04. Repositório e relatório completo na descrição. Obrigado!"

**Na tela:** link do repo + nomes dos integrantes.

---

## Checklist final de gravação

- [ ] Cada integrante gravou seu trecho
- [ ] Os slides estão na ordem certa e sem typo
- [ ] A demo do Gabriel foi feita ao vivo (não captura de tela estática)
- [ ] O áudio está audível em todos os trechos
- [ ] Duração total entre 5 e 10 minutos
- [ ] Arquivo final em formato compatível com a plataforma de entrega
