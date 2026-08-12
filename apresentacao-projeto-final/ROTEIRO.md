# Roteiro do Vídeo — Projeto Final (Compilador Fun estendido)

**Disciplina:** Construção de Compiladores 1
**Projeto Final:** três extensões simples sobre a linguagem Fun (Atividade 10)
**Duração-alvo:** ~7:00 (margem para 5–10 min)

## Divisão por integrante

| Integrante              | Bloco                                                        | Tempo  | Slides   |
|--------------------------|---------------------------------------------------------------|--------|----------|
| **Davi**                | Introdução + recapinho rápido do que já tínhamos              | ~1:00  | 1–3      |
| **Nathan**               | Extensão 1 (comparações) + Extensão 2 (atribuição composta)  | ~2:00  | 4–6      |
| **João Vitor**           | Extensão 3 — return dentro de if/while                        | ~2:00  | 7–9      |
| **Gabriel**              | Demo das três juntas + testes                                 | ~1:45  | 10–12    |
| (qualquer um)            | Encerramento                                                  | ~0:15  | 13       |

## Dicas gerais de gravação

- Mesmo esquema do Marco 1: cada um grava seu trecho separado, webcam num canto, slides ocupando o resto.
- **Tom da conversa: falar como se estivesse explicando pra um colega, não lendo um relatório.** Evitar despejar termo técnico atrás de termo técnico — quando precisar usar um (tipo "lookahead" ou "açúcar sintático"), explicar em uma frase simples o que aquilo quer dizer na prática.
- **O foco do vídeo é o que a gente ACRESCENTOU.** O recap do Marco 1 (slide 2) é rápido de propósito — ninguém precisa reexplicar o compilador inteiro de novo, o interessante aqui são as três coisas novas.
- A demo do Gabriel (slide 10) é o momento mais importante do vídeo — mostrar o código rodando vale mais que qualquer slide bonito.
- Se sobrar pouco tempo, pode cortar o slide 6 (o "porquê" da decisão de projeto) e resumir em uma frase dentro do slide 5.

---

## Slide 1 — Capa
**Quem fala:** Davi
**Tempo:** ~0:15

> "Oi, professor! A gente é o grupo do Davi, Gabriel, João Vitor e Nathan, e hoje vamos mostrar o Projeto Final: três coisas novas que a gente adicionou no compilador Fun que já tínhamos pronto da Atividade 10."

**Na tela:** slide com título, integrantes, disciplina, professor.

---

## Slide 2 — De onde a gente partiu
**Quem fala:** Davi
**Tempo:** ~0:30

> "Rapidinho pra situar: no Marco 1 a gente mostrou um compilador bem simples, só de expressões com números. Desde então fomos evoluindo isso atividade por atividade, até chegar num compilador de verdade — com variáveis, if, while, e na última atividade, funções, com parâmetros e até recursão. O Projeto Final é a gente pegando esse compilador de funções e deixando ele um pouco mais completo."

**Na tela:** linha do tempo bem simples: expressões → variáveis → if/while → funções → **Projeto Final**.

---

## Slide 3 — O que a gente escolheu adicionar
**Quem fala:** Davi
**Tempo:** ~0:30

> "O enunciado dava várias opções de coisas pra adicionar. A gente escolheu três, que achamos que deixam a linguagem bem mais fácil de programar de verdade: comparações novas, tipo `menor ou igual`; um jeito mais curto de fazer conta e guardar de volta na mesma variável; e a possibilidade de sair de uma função mais cedo com `return`, sem precisar esperar chegar no fim dela. Bora mostrar cada uma."

**Na tela:** as três extensões em destaque, como uma lista simples: "1. Comparações novas · 2. Atalho pra somar/subtrair direto na variável · 3. Sair de uma função mais cedo".

---

## Slide 4 — Comparações novas
**Quem fala:** Nathan
**Tempo:** ~0:45

> "A primeira coisa que a gente adicionou foram três comparações que a linguagem não tinha: `menor ou igual`, `maior ou igual` e `diferente`. Antes, se você quisesse testar 'menor ou igual', tinha que escrever de um jeito meio torto, combinando outras comparações. Agora dá pra escrever direto. Por trás dos panos foi bem tranquilo de fazer: a gente só ensinou o compilador a reconhecer esses símbolos novos, e reaproveitou praticamente todo o código que já traduzia as comparações antigas."

**Na tela:** um `if` usando `<=` e `>=` de um jeito natural, tipo classificar uma nota ou idade.

---

## Slide 5 — Um atalho pra atualizar variáveis
**Quem fala:** Nathan
**Tempo:** ~0:45

> "A segunda coisa foi um atalho bem comum em várias linguagens: em vez de escrever `total = total + 5`, agora dá pra escrever só `total += 5`. Mesma coisa pra subtração, multiplicação e divisão. Isso deixa o código bem mais limpo, principalmente dentro de laços, onde você fica atualizando a mesma variável várias vezes."

**Na tela:** lado a lado, `total += 5;` e `total = total + 5;`, com uma seta mostrando que dá exatamente no mesmo resultado.

---

## Slide 6 — Um detalhe legal dessa implementação
**Quem fala:** Nathan
**Tempo:** ~0:20

> "Um detalhe que achamos interessante: a gente não criou nada novo por trás — o `+=` simplesmente vira, na hora de compilar, a mesma coisa que `total = total + 5`. Ou seja, zero código novo pra gerar o assembly disso, só reaproveitamos o que já existia. E testamos justamente isso: que as duas formas geram o mesmo resultado, sem nenhuma diferença."

**Na tela:** frase curta em destaque: "x += 5 vira exatamente x = x + 5 por baixo dos panos."

---

## Slide 7 — Saindo de uma função mais cedo
**Quem fala:** João Vitor
**Tempo:** ~0:35

> "A terceira e mais legal das três: antes, uma função só podia terminar com um `return` bem no finalzinho dela. Se você quisesse sair mais cedo — por exemplo, dentro de um `if` — não dava. Tinha que usar uma variável auxiliar pra guardar o resultado até chegar no fim. Agora a gente pode simplesmente escrever `return` ali dentro do `if`, e a função já encerra ali, devolvendo aquele valor na hora."

**Na tela:** um exemplo simples tipo "checar o sinal de um número", mostrando quanto o código fica mais direto com `return` dentro do `if`.

---

## Slide 8 — O desafio de fazer isso funcionar
**Quem fala:** João Vitor
**Tempo:** ~0:40

> "O desafio aqui foi que, antes, `return` só existia em um lugar bem específico: o finalzinho da função. Agora ele podia aparecer em vários lugares diferentes, e o compilador precisava saber diferenciar: 'esse `return` aqui é o que encerra a função de vez, ou é um dos que aparecem no meio do caminho?'. A solução foi bem simples na prática: o compilador olha o que vem logo depois daquele `return` — se for o fechamento da função, é o último mesmo; se não for, é um dos antecipados, e ele continua lendo o resto normalmente."

**Na tela:** o mesmo exemplo do slide anterior, com uma seta apontando "esse aqui é antecipado" e outra "esse aqui é o de verdade, o último".

---

## Slide 9 — Como isso vira código de máquina
**Quem fala:** João Vitor
**Tempo:** ~0:30

> "Na prática, cada função ganhou um 'ponto de saída' fixo no código gerado. Quando um `return` antecipado acontece, ele simplesmente pula direto pra esse ponto de saída, sem passar pelo resto da função. É basicamente um atalho dentro do próprio código de máquina, do mesmo jeito que a gente faz na cabeça quando pensa 'ah, já achei a resposta, posso parar por aqui'."

**Na tela:** bem simples: uma seta saindo do meio da função e indo direto pro fim, ignorando o resto.

---

## Slide 10 — Mostrando tudo funcionando junto
**Quem fala:** Gabriel
**Tempo:** ~0:55

> "Bom, chega de falar, bora ver funcionando. Fiz um programinha que usa as três coisas ao mesmo tempo: ele classifica um número em três faixas, usando as comparações novas; sai da função mais cedo com `return` assim que descobre a resposta; e usa o `+=` pra ir somando um contador. Vou compilar aqui e mostrar o resultado."

**Na tela:** o código-fonte de um lado, o comando `python compfun.py ...` rodando, e o resultado final aparecendo (imprime `3`).

---

## Slide 11 — E continua tudo funcionando como antes
**Quem fala:** Gabriel
**Tempo:** ~0:35

> "E o mais importante: a gente não quebrou nada do que já existia. Todos os testes que já tínhamos da Atividade 10 continuam passando exatamente igual, e ainda escrevemos um bocado de testes novos só pras três coisas que adicionamos — no total, 66 testes, todos passando."

**Na tela:** terminal rodando os testes, mostrando `Ran 66 tests ... OK`.

---

## Slide 12 — Por que só essas três
**Quem fala:** Gabriel
**Tempo:** ~0:20

> "O enunciado dava a opção de fazer uma coisa mais complexa, ou pelo menos três mais simples. A gente preferiu as três simples, porque são mudanças que realmente ajudam quem for programar na linguagem, sem precisar reinventar um monte de coisa por trás — deu pra fazer com calma e testar direito tudo o que mudou."

**Na tela:** as três extensões escolhidas, simples e direto.

---

## Slide 13 — Encerramento
**Quem fala:** (qualquer um, sugerimos Davi)
**Tempo:** ~0:15

> "É isso! Deixamos o compilador Fun um pouco mais completo com essas três novidades. O código todo, com os testes e a documentação, tá no repositório na descrição. Valeu, professor!"

**Na tela:** link do repo + nomes dos integrantes.

---

## Checklist final de gravação

- [ ] Cada integrante gravou seu trecho
- [ ] Os slides estão na ordem certa e sem typo
- [ ] A demo do Gabriel foi feita ao vivo (não captura de tela estática)
- [ ] O áudio está audível em todos os trechos
- [ ] Duração total entre 5 e 10 minutos
- [ ] Arquivo final em formato compatível com a plataforma de entrega
