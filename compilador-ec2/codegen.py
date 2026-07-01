"""Gerador de codigo x86-64 (sintaxe GNU Assembler) para a AST EC1.

Esquema de traducao baseado na pilha (secao 4 do enunciado), usando a ordem
INVERTIDA dos operandos (opcao 2 da secao 4.1, pagina 9): primeiro o codigo
do operando direito (empilhado), depois o do esquerdo. Apos o `pop %rbx`,
%rax tem o operando esquerdo e %rbx tem o direito -- ordem correta para os
operadores nao-comutativos (sub, idiv) sem nenhum truque adicional.

Tradução:
    Const(n)            -> mov $n, %rax
    OpBin(op, esq, dir) -> codigo(dir)
                           push %rax
                           codigo(esq)
                           pop %rbx
                           <instrucao do operador, com %rbx, %rax>

Operadores:
    SOMA -> add  %rbx, %rax
    SUB  -> sub  %rbx, %rax
    MULT -> imul %rbx, %rax
    DIV  -> cqo + idiv %rbx     (rdx:rax / rbx; quociente em %rax)

O modelo completo de saida (secao 5) e o mesmo da Atividade 02.
"""

from __future__ import annotations

from ast_ec1 import Const, Exp, Op, OpBin


# Mapa entre Op (enum da AST) e mnemonico assembly da operacao.
# DIV recebe tratamento especial em _emit_op (precisa de `cqo`).
_OP_INSTR: dict[Op, str] = {
    Op.SOMA: "add",
    Op.SUB: "sub",
    Op.MULT: "imul",
}


TEMPLATE = """\
#
# Saida gerada pelo compilador EC1
#
    .section .text
    .globl _start

_start:
{corpo}
    call imprime_num
    call sair

    .include "runtime.s"
"""


class GeradorDeCodigo:
    """Acumula instrucoes assembly enquanto varre a AST."""

    INDENT = "    "

    def __init__(self) -> None:
        self._linhas: list[str] = []

    # ----- API publica -----

    def gerar(self, arvore: Exp) -> str:
        """Retorna o codigo da expressao (apenas o corpo, sem o template)."""
        self._linhas.clear()
        self._emit_exp(arvore)
        return "\n".join(self._linhas)

    def gerar_programa(self, arvore: Exp) -> str:
        """Retorna o arquivo .s completo, ja embrulhado no modelo de saida."""
        corpo = self.gerar(arvore)
        # adiciona indentacao consistente a cada linha do corpo
        corpo_indentado = "\n".join(
            self.INDENT + linha if linha else linha for linha in corpo.split("\n")
        )
        return TEMPLATE.format(corpo=corpo_indentado)

    # ----- visitacao -----

    def _emit_exp(self, no: Exp) -> None:
        if isinstance(no, Const):
            self._emit(f"mov ${no.valor}, %rax")
            return
        if isinstance(no, OpBin):
            # Ordem invertida: codigo do operando direito primeiro,
            # empilha, depois codigo do operando esquerdo.
            self._emit_exp(no.dir)
            self._emit("push %rax")
            self._emit_exp(no.esq)
            self._emit("pop %rbx")
            self._emit_op(no.op)
            return
        raise TypeError(f"no de AST desconhecido: {type(no).__name__}")

    def _emit_op(self, op: Op) -> None:
        if op is Op.DIV:
            # idiv divide rdx:rax por src; precisa de cqo para
            # estender o sinal de rax em rdx antes da divisao.
            self._emit("cqo")
            self._emit("idiv %rbx")
            return
        instr = _OP_INSTR.get(op)
        if instr is None:
            raise RuntimeError(f"operador sem traducao definida: {op}")
        self._emit(f"{instr} %rbx, %rax")

    def _emit(self, linha: str) -> None:
        self._linhas.append(linha)


# ----- atalhos funcionais -----

def gerar_codigo(arvore: Exp) -> str:
    """Gera apenas o codigo da expressao (sem o template)."""
    return GeradorDeCodigo().gerar(arvore)


def gerar_programa(arvore: Exp) -> str:
    """Gera o arquivo .s completo, pronto para ser montado."""
    return GeradorDeCodigo().gerar_programa(arvore)


__all__ = ["GeradorDeCodigo", "gerar_codigo", "gerar_programa", "TEMPLATE"]
