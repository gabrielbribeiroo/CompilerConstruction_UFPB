"""Gerador de codigo x86-64 (sintaxe GNU Assembler) para a AST EV.

Reaproveita o esquema de pilha das Atividades 06/07 para expressoes
(Const/OpBin), estendido com:

    Var(nome)  -> mov <nome>, %rax        (le a variavel da memoria)

e com a geracao do programa completo, que agora tem duas partes:

    1. secao .bss: uma diretiva `.lcomm <nome>, 8` por variavel
       declarada (8 bytes = inteiro de 64 bits), sem duplicar entradas
       mesmo que a mesma variavel seja atribuida mais de uma vez;
    2. secao .text: o codigo de cada declaracao (codigo da expressao
       seguido de `mov %rax, <nome>` para gravar o resultado), em
       ordem, seguido do codigo da expressao final.

Tradução das expressoes (identica as Atividades 06/07):
    Const(n)            -> mov $n, %rax
    Var(nome)           -> mov <nome>, %rax
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
"""

from __future__ import annotations

from ast_ev import Const, Exp, Op, OpBin, Programa, Var


_OP_INSTR: dict[Op, str] = {
    Op.SOMA: "add",
    Op.SUB: "sub",
    Op.MULT: "imul",
}


TEMPLATE = """\
#
# Saida gerada pelo compilador EV
#
    .section .bss
{bss}
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

    def gerar_codigo_exp(self, exp: Exp) -> str:
        """Retorna o codigo de uma unica expressao (sem template)."""
        self._linhas = []
        self._emit_exp(exp)
        return "\n".join(self._linhas)

    def gerar_programa(self, programa: Programa) -> str:
        """Retorna o arquivo .s completo, ja embrulhado no modelo de saida."""
        variaveis = self._coleta_variaveis(programa)
        bss = "\n".join(
            f"{self.INDENT}.lcomm {nome}, 8" for nome in variaveis
        )

        self._linhas = []
        for decl in programa.declaracoes:
            self._emit(f"# {decl.nome} = {decl.exp};")
            self._emit_exp(decl.exp)
            self._emit(f"mov %rax, {decl.nome}")
        self._emit(f"# = {programa.exp_final}")
        self._emit_exp(programa.exp_final)
        corpo = "\n".join(self._linhas)

        corpo_indentado = "\n".join(
            self.INDENT + linha if linha else linha for linha in corpo.split("\n")
        )
        return TEMPLATE.format(bss=bss, corpo=corpo_indentado)

    # ----- coleta de simbolos -----

    @staticmethod
    def _coleta_variaveis(programa: Programa) -> list[str]:
        """Nomes das variaveis declaradas, na ordem de primeira declaracao,
        sem duplicatas (uma variavel reatribuida so gera um .lcomm)."""
        vistas: dict[str, None] = {}
        for decl in programa.declaracoes:
            vistas.setdefault(decl.nome, None)
        return list(vistas.keys())

    # ----- visitacao de expressoes -----

    def _emit_exp(self, no: Exp) -> None:
        if isinstance(no, Const):
            self._emit(f"mov ${no.valor}, %rax")
            return
        if isinstance(no, Var):
            self._emit(f"mov {no.nome}, %rax")
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

def gerar_programa(programa: Programa) -> str:
    """Gera o arquivo .s completo, pronto para ser montado."""
    return GeradorDeCodigo().gerar_programa(programa)


__all__ = ["GeradorDeCodigo", "gerar_programa", "TEMPLATE"]
