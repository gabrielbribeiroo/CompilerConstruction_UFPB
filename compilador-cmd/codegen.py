"""Gerador de codigo x86-64 (sintaxe GNU Assembler) para a AST Cmd.

Reaproveita o esquema de pilha das Atividades 06-08 para expressoes
(Const/Var/OpBin aritmetico) e estende com:

    - operadores de comparacao (secao 6.1 do enunciado): cmp + setz/
      setl/setg, usando %rcx como temporario de 8 bits;
    - comandos (secao 6.2 do enunciado): Atrib gera o codigo da
      expressao seguido de um mov para a variavel; If e While usam
      cmp $0, %rax + jz + rotulos com um contador incremental para
      gerar nomes unicos (Lfalso0, Lfim0, Linicio1, Lfim1, ...).

Traducao de expressoes (identica as atividades anteriores):
    Const(n)            -> mov $n, %rax
    Var(nome)           -> mov <nome>, %rax
    OpBin(op, esq, dir) -> codigo(dir)
                           push %rax
                           codigo(esq)
                           pop %rbx
                           <instrucao(oes) do operador, com %rbx, %rax>

Operadores aritmeticos:
    SOMA -> add  %rbx, %rax
    SUB  -> sub  %rbx, %rax
    MULT -> imul %rbx, %rax
    DIV  -> cqo + idiv %rbx

Operadores de comparacao (secao 6.1): apos o pop, %rax tem o operando
esquerdo e %rbx o direito -- exatamente a ordem usada no exemplo do
enunciado para "A == B" (rax=A, rbx=B), entao reaproveitamos o mesmo
esquema de pilha sem nenhuma adaptacao:
    MENOR -> xor %rcx,%rcx; cmp %rbx,%rax; setl %cl; mov %rcx,%rax
    MAIOR -> xor %rcx,%rcx; cmp %rbx,%rax; setg %cl; mov %rcx,%rax
    IGUAL -> xor %rcx,%rcx; cmp %rbx,%rax; setz %cl; mov %rcx,%rax
"""

from __future__ import annotations

from ast_cmd import Atrib, Cmd, Const, Exp, If, Op, OpBin, Programa, Var, While


_OP_ARITMETICO: dict[Op, str] = {
    Op.SOMA: "add",
    Op.SUB: "sub",
    Op.MULT: "imul",
}

_OP_COMPARACAO: dict[Op, str] = {
    Op.MENOR: "setl",
    Op.MAIOR: "setg",
    Op.IGUAL: "setz",
}


TEMPLATE = """\
#
# Saida gerada pelo compilador Cmd
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
        self._contador_rotulos = 0

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
        self._contador_rotulos = 0
        for decl in programa.declaracoes:
            self._emit(f"# {decl.nome} = {decl.exp};")
            self._emit_exp(decl.exp)
            self._emit(f"mov %rax, {decl.nome}")
        for cmd in programa.comandos:
            self._emit_cmd(cmd)
        self._emit(f"# return {programa.exp_final};")
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

    # ----- visitacao de comandos -----

    def _emit_cmd(self, cmd: Cmd) -> None:
        if isinstance(cmd, Atrib):
            self._emit(f"# {cmd.nome} = {cmd.exp};")
            self._emit_exp(cmd.exp)
            self._emit(f"mov %rax, {cmd.nome}")
            return
        if isinstance(cmd, If):
            n = self._proximo_rotulo()
            lfalso, lfim = f"Lfalso{n}", f"Lfim{n}"
            self._emit(f"# if {cmd.cond} {{")
            self._emit_exp(cmd.cond)
            self._emit("cmp $0, %rax")
            self._emit(f"jz {lfalso}")
            for c in cmd.cmds_then:
                self._emit_cmd(c)
            self._emit(f"jmp {lfim}")
            self._emit(f"{lfalso}:")
            self._emit("# } else {")
            for c in cmd.cmds_else:
                self._emit_cmd(c)
            self._emit(f"{lfim}:")
            self._emit("# }")
            return
        if isinstance(cmd, While):
            n = self._proximo_rotulo()
            linicio, lfim = f"Linicio{n}", f"Lfim{n}"
            self._emit(f"{linicio}:")
            self._emit(f"# while {cmd.cond} {{")
            self._emit_exp(cmd.cond)
            self._emit("cmp $0, %rax")
            self._emit(f"jz {lfim}")
            for c in cmd.cmds:
                self._emit_cmd(c)
            self._emit(f"jmp {linicio}")
            self._emit(f"{lfim}:")
            self._emit("# }")
            return
        raise TypeError(f"no de comando desconhecido: {type(cmd).__name__}")

    def _proximo_rotulo(self) -> int:
        n = self._contador_rotulos
        self._contador_rotulos += 1
        return n

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
            # empilha, depois codigo do operando esquerdo. Apos o pop,
            # %rax = esq e %rbx = dir (para aritmetica e comparacao).
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
        instr_aritmetico = _OP_ARITMETICO.get(op)
        if instr_aritmetico is not None:
            self._emit(f"{instr_aritmetico} %rbx, %rax")
            return
        instr_comparacao = _OP_COMPARACAO.get(op)
        if instr_comparacao is not None:
            self._emit("xor %rcx, %rcx")
            self._emit("cmp %rbx, %rax")
            self._emit(f"{instr_comparacao} %cl")
            self._emit("mov %rcx, %rax")
            return
        raise RuntimeError(f"operador sem traducao definida: {op}")

    def _emit(self, linha: str) -> None:
        self._linhas.append(linha)


# ----- atalhos funcionais -----

def gerar_programa(programa: Programa) -> str:
    """Gera o arquivo .s completo, pronto para ser montado."""
    return GeradorDeCodigo().gerar_programa(programa)


__all__ = ["GeradorDeCodigo", "gerar_programa", "TEMPLATE"]
