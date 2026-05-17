; =============================================================
; Congruência de Zeller – Assembly x86-64 (Linux, NASM)
; Atividade 03 – Andrei Formiga
;
; Entradas (definidas na seção de teste abaixo):
;   R8  = q  (dia do mês)
;   R9  = m  (mês ajustado: 3=março … 14=fevereiro)
;   R10 = k  (ano dentro do século, ex: 26 para 2026)
;   R11 = j  (século, ex: 20 para 2026)
;
; Fórmula:
;   h = (q + floor(13*(m+1)/5) + k + floor(k/4)
;           + floor(j/4) - 2*j) mod 7
;
; Saída:
;   RAX = h  (0=sáb, 1=dom, 2=seg, 3=ter, 4=qua, 5=qui, 6=sex)
; =============================================================

section .data
    ; Strings para impressão
    msg_result  db  "Dia da semana (h) = ", 0
    msg_newline db  10, 0
    days        db  "Sabado", 0
                db  "Domingo", 0
                db  "Segunda-feira", 0
                db  "Terca-feira", 0
                db  "Quarta-feira", 0
                db  "Quinta-feira", 0
                db  "Sexta-feira", 0

    ; -------------------------------------------------------
    ; Valores de teste: 16/05/2026 (sexta-feira)
    ;   q = 16, m = 5, ano = 2026  →  j = 20, k = 26
    ; -------------------------------------------------------
    test_q  dq  16      ; dia
    test_m  dq  5       ; mês (maio = 5, já está entre 3-14)
    test_k  dq  26      ; ano dentro do século
    test_j  dq  20      ; século

section .text
    global _start

; -------------------------------------------------------------
; _start: carrega os valores de teste e chama zeller
; -------------------------------------------------------------
_start:
    ; Carregar entradas nos registradores definidos pela atividade
    mov  R8,  [test_q]
    mov  R9,  [test_m]
    mov  R10, [test_k]
    mov  R11, [test_j]

    ; Chamar a função que calcula a congruência
    call zeller

    ; RAX agora contém h (0-6)
    ; Encerrar o processo com h como código de saída (para depuração fácil)
    mov  RDI, RAX
    mov  RAX, 60        ; syscall exit
    syscall

; -------------------------------------------------------------
; zeller: calcula a congruência de Zeller
;
; Entradas: R8=q, R9=m, R10=k, R11=j
; Saída:    RAX = h  (0-6)
; Registradores modificados: RAX, RBX, RCX, RDX
; -------------------------------------------------------------
zeller:
    ; Preservar registradores que não são caller-saved
    push RBX
    push RCX

    ; -----------------------------------------------------------
    ; Passo 1: calcular floor(13*(m+1)/5)
    ;   term1 = (R9 + 1) * 13 / 5   (divisão inteira)
    ; -----------------------------------------------------------
    mov  RAX, R9            ; RAX = m
    add  RAX, 1             ; RAX = m + 1
    imul RAX, 13            ; RAX = 13*(m+1)
    cqo                     ; sign-extend RAX → RDX:RAX
    mov  RBX, 5
    idiv RBX                ; RAX = floor(13*(m+1)/5)
    mov  RCX, RAX           ; RCX = term1  (guarda para depois)

    ; -----------------------------------------------------------
    ; Passo 2: calcular floor(k/4)
    ; -----------------------------------------------------------
    mov  RAX, R10           ; RAX = k
    cqo
    mov  RBX, 4
    idiv RBX                ; RAX = floor(k/4)
    add  RCX, RAX           ; RCX += floor(k/4)

    ; -----------------------------------------------------------
    ; Passo 3: calcular floor(j/4)
    ; -----------------------------------------------------------
    mov  RAX, R11           ; RAX = j
    cqo
    mov  RBX, 4
    idiv RBX                ; RAX = floor(j/4)
    add  RCX, RAX           ; RCX += floor(j/4)

    ; -----------------------------------------------------------
    ; Passo 4: montar o numerador completo
    ;   soma = q + term1 + k + floor(k/4) + floor(j/4) - 2*j
    ; -----------------------------------------------------------
    add  RCX, R8            ; RCX += q
    add  RCX, R10           ; RCX += k

    mov  RAX, R11           ; RAX = j
    imul RAX, 2             ; RAX = 2*j
    sub  RCX, RAX           ; RCX -= 2*j

    ; -----------------------------------------------------------
    ; Passo 5: h = soma mod 7
    ;   IDIV pode retornar resto negativo em C; precisamos garantir
    ;   que o resultado fique em [0, 6].
    ; -----------------------------------------------------------
    mov  RAX, RCX
    cqo
    mov  RBX, 7
    idiv RBX                ; RDX = RAX mod 7  (pode ser negativo)

    ; Corrigir resto negativo: se RDX < 0, somar 7
    cmp  RDX, 0
    jge  .done
    add  RDX, 7

.done:
    mov  RAX, RDX           ; retornar h em RAX

    pop  RCX
    pop  RBX
    ret
