#
# runtime.s - rotinas de runtime usadas pelo modelo de saida do compilador CI
#
# Define dois procedimentos chamados pelo modelo gerado:
#   - imprime_num: imprime o valor em %rax como inteiro decimal (sem sinal),
#                  seguido de uma quebra de linha, em stdout
#   - sair:        encerra o processo com codigo de saida 0
#
# Linux x86-64, sintaxe do GNU Assembler.
#

    .section .bss
buffer:
    .skip 32

    .section .text

    .globl imprime_num
imprime_num:
    pushq %rbx
    pushq %rcx
    pushq %rdx
    pushq %rsi
    pushq %rdi

    leaq buffer+31(%rip), %rcx      # rcx aponta para o ultimo byte do buffer
    movb $10, (%rcx)                # coloca '\n' no final
    movq $1, %rbx                   # tamanho da string a escrever (so o \n)

    testq %rax, %rax                # caso especial: rax == 0
    jnz .Lconv_loop
    decq %rcx
    movb $'0', (%rcx)
    incq %rbx
    jmp .Lconv_write

.Lconv_loop:
    testq %rax, %rax
    jz .Lconv_write
    xorq %rdx, %rdx
    movq $10, %rsi
    divq %rsi                       # rax = rax/10, rdx = rax%10
    addb $'0', %dl
    decq %rcx
    movb %dl, (%rcx)
    incq %rbx
    jmp .Lconv_loop

.Lconv_write:
    movq $1, %rax                   # sys_write
    movq $1, %rdi                   # fd = stdout
    movq %rcx, %rsi                 # buffer
    movq %rbx, %rdx                 # tamanho
    syscall

    popq %rdi
    popq %rsi
    popq %rdx
    popq %rcx
    popq %rbx
    ret

    .globl sair
sair:
    movq $60, %rax                  # sys_exit
    xorq %rdi, %rdi                 # status = 0
    syscall
