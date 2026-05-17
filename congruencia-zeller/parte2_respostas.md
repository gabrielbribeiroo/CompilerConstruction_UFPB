# Relatório - Atividade 03 - Congruência de Zeller (Assembly)

**Universidade Federal da Paraíba (UFPB)**
**Centro de Informática - Curso de Ciência da Computação**
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

## Pergunta 1

**Qual o menor número de registradores necessários para calcular a₁ + a₂ + … + aₙ?**

**Resposta: 1 registrador.**

Como todos os valores são constantes inteiras, basta acumular a soma em um único registrador:

```asm
mov RAX, a1
add RAX, a2
add RAX, a3
...
add RAX, an
```

Cada instrução `add` usa um imediato (constante embutida na própria instrução), sem necessitar de nenhum registrador extra.

---

## Pergunta 2

**Qual o menor número de registradores necessários para calcular (a₁₁ × … × a₁ₙ) + … + (aₘ₁ × … × aₘₙ)?**

**Resposta: 2 registradores.**

Um registrador acumula o **produto** do grupo atual e o outro acumula a **soma total** dos grupos. Ao terminar cada grupo, o produto é somado ao acumulador total e o registrador de produto é reiniciado para o próximo grupo:

```asm
mov RAX, 0          ; acumulador da soma total
; --- grupo 1 ---
mov RBX, a11
imul RBX, a12
...
imul RBX, a1n
add RAX, RBX        ; soma o produto do grupo 1
; --- grupo 2 ---
mov RBX, a21
...
add RAX, RBX        ; soma o produto do grupo 2
...
```

Com apenas 1 registrador não seria possível: ao calcular o produto de um grupo, o valor acumulado da soma seria sobrescrito.

---

## Pergunta 3

**O número de registradores pode crescer sem limite para expressões aritméticas arbitrárias?**

**Resposta: Não. Um número fixo e pequeno de registradores é sempre suficiente.**

Qualquer expressão aritmética pode ser representada como uma **árvore de expressão**, onde as folhas são constantes e os nós internos são operações. Essa árvore pode sempre ser avaliada usando a **pilha de memória** como extensão dos registradores: quando um registrador é necessário mas todos estão ocupados, o valor atual é salvo na pilha (`push`) e recuperado depois (`pop`).

Na prática, o número de registradores necessários sem usar a pilha é determinado pela **altura da árvore da expressão** (pelo algoritmo de Sethi-Ullman), e esse número pode crescer com expressões profundamente aninhadas. Porém, como a pilha é ilimitada, **2 registradores + pilha** são suficientes para qualquer expressão de tamanho arbitrário. Portanto, o número de registradores não precisa crescer sem limite.
