"""Gerador de codigo x86-64 (sintaxe GNU Assembler) para a AST Fun.

Reaproveita o esquema de pilha das Atividades 06-09 para expressoes
(Const/Var/OpBin) e comandos (Atrib/If/While com rotulos), e estende
com a convencao de chamada de funcoes descrita nas secoes 6 e 7 do
enunciado.

Convencao de chamada adotada (secao 6.1):

    - Parametros sao passados pela pilha, empilhados na ORDEM INVERSA
      (ultimo parametro primeiro), antes do CALL; a funcao chamada
      remove os parametros criando seu proprio registro de ativacao,
      e o CHAMADOR remove os parametros da pilha apos o CALL.
    - O valor de retorno da funcao fica em %rax (mesma convencao ja
      usada para expressoes desde a Atividade 06).
    - Cada funcao usa RBP como *frame pointer*: o prologo empilha o
      RBP anterior, aloca espaco para as variaveis locais com SUB, e
      copia RSP para RBP -- NESSA ORDEM. Por causa dessa ordem, RBP
      acaba apontando para o INICIO das variaveis locais (nao para o
      slot onde o RBP antigo foi salvo, como na convencao classica de
      `leave`); o epilogo por isso soma L*8 a RSP antes de dar POP em
      RBP, exatamente como os passos 8-9 da secao 6.1.4 do enunciado
      (a instrucao LEAVE do x86 NAO seria equivalente aqui: ela so
      funciona quando RBP aponta diretamente para o slot salvo, o que
      só e verdade quando a funcao nao tem variaveis locais).
    - Uma variavel local de indice j (0-based, na ordem declarada) fica
      em `8*j(%rbp)`; um parametro de indice i (0-based, na ordem
      declarada) fica em `(8*L + 16 + 8*i)(%rbp)`, onde L e o numero
      de variaveis locais da funcao (os 16 bytes cobrem o RBP salvo e
      o endereco de retorno empilhados pelo prologo/CALL).

Tradução de expressoes (identica as atividades anteriores, exceto
Chamada, que e nova):
    Const(n)            -> mov $n, %rax
    Var(nome)            -> mov <nome>, %rax               (global)
                          | mov <desloc>(%rbp), %rax        (local)
    OpBin(op, esq, dir)  -> codigo(dir); push %rax; codigo(esq); pop %rbx; <op>
    Chamada(nome, args)  -> para cada arg em ordem inversa: codigo(arg); push %rax
                            call <nome>
                            add $8*len(args), %rsp   (omitido se len(args) == 0)
"""

from __future__ import annotations

from ast_fun import (
    Atrib,
    Chamada,
    Cmd,
    Const,
    Exp,
    FunDecl,
    If,
    Op,
    OpBin,
    Programa,
    Var,
    VarDecl,
    While,
)


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
# Saida gerada pelo compilador Fun
#
    .section .bss
{bss}
    .section .text
    .globl _start

_start:
{corpo_principal}
    call imprime_num
    call sair

{corpo_funcoes}
    .include "runtime.s"
"""


class GeradorDeCodigo:
    """Acumula instrucoes assembly enquanto varre a AST.

    Mantem um mapa `nome -> deslocamento(%rbp)` ativo apenas durante a
    geracao do corpo da funcao atual (`self._quadro`); fora desse
    contexto (bloco main), `self._quadro` e None e toda referencia a
    variavel usa a secao BSS global.
    """

    INDENT = "    "

    def __init__(self) -> None:
        self._linhas: list[str] = []
        self._contador_rotulos = 0
        self._quadro: dict[str, int] | None = None

    # ----- API publica -----

    def gerar_codigo_exp(self, exp: Exp) -> str:
        """Retorna o codigo de uma unica expressao (sem template)."""
        self._linhas = []
        self._emit_exp(exp)
        return "\n".join(self._linhas)

    def gerar_programa(self, programa: Programa) -> str:
        """Retorna o arquivo .s completo, ja embrulhado no modelo de saida."""
        variaveis = self._coleta_variaveis_globais(programa)
        bss = "\n".join(f"{self.INDENT}.lcomm {nome}, 8" for nome in variaveis)

        # 1. corpo do bloco principal
        self._linhas = []
        self._quadro = None
        self._contador_rotulos = 0
        for decl in programa.declaracoes:
            if isinstance(decl, VarDecl):
                self._emit(f"# var {decl.nome} = {decl.exp};")
                self._emit_exp(decl.exp)
                self._emit_armazena_variavel(decl.nome)
        for cmd in programa.comandos:
            self._emit_cmd(cmd)
        self._emit(f"# return {programa.exp_final};")
        self._emit_exp(programa.exp_final)
        corpo_principal = self._formata_bloco(self._linhas)

        # 2. corpo de cada funcao declarada
        blocos_funcoes: list[str] = []
        for decl in programa.declaracoes:
            if isinstance(decl, FunDecl):
                blocos_funcoes.append(self._gerar_funcao(decl))
        corpo_funcoes = "\n\n".join(blocos_funcoes)

        return TEMPLATE.format(
            bss=bss, corpo_principal=corpo_principal, corpo_funcoes=corpo_funcoes
        )

    # ----- coleta de simbolos -----

    @staticmethod
    def _coleta_variaveis_globais(programa: Programa) -> list[str]:
        """Nomes das variaveis GLOBAIS declaradas, na ordem de primeira
        declaracao, sem duplicatas."""
        vistas: dict[str, None] = {}
        for decl in programa.declaracoes:
            if isinstance(decl, VarDecl):
                vistas.setdefault(decl.nome, None)
        return list(vistas.keys())

    @staticmethod
    def _calcula_quadro(fundecl: FunDecl) -> dict[str, int]:
        """Calcula o deslocamento (relativo a %rbp) de cada variavel
        local e parametro da funcao, conforme a secao 6.1.3 do
        enunciado."""
        quadro: dict[str, int] = {}
        n_locais = len(fundecl.vardecls)
        for j, vd in enumerate(fundecl.vardecls):
            quadro[vd.nome] = 8 * j
        for i, nome_param in enumerate(fundecl.params):
            quadro[nome_param] = 8 * n_locais + 16 + 8 * i
        return quadro

    # ----- geracao do corpo de uma funcao -----

    def _gerar_funcao(self, fundecl: FunDecl) -> str:
        self._linhas = []
        self._quadro = self._calcula_quadro(fundecl)
        n_locais = len(fundecl.vardecls)

        self._emit(f"{fundecl.nome}:")
        self._emit("push %rbp")
        if n_locais > 0:
            self._emit(f"sub ${8 * n_locais}, %rsp")
        self._emit("mov %rsp, %rbp")

        for j, vd in enumerate(fundecl.vardecls):
            self._emit(f"# var {vd.nome} = {vd.exp};")
            self._emit_exp(vd.exp)
            self._emit(f"mov %rax, {8 * j}(%rbp)")

        for cmd in fundecl.comandos:
            self._emit_cmd(cmd)

        self._emit(f"# return {fundecl.exp_final};")
        self._emit_exp(fundecl.exp_final)

        if n_locais > 0:
            self._emit(f"add ${8 * n_locais}, %rsp")
        self._emit("pop %rbp")
        self._emit("ret")

        self._quadro = None
        return self._formata_bloco(self._linhas)

    def _formata_bloco(self, linhas: list[str]) -> str:
        """Indenta cada linha do bloco, exceto rotulos (que ficam na
        coluna 0, seguindo a convencao do GNU Assembler)."""
        formatadas = []
        for linha in linhas:
            if linha and linha.endswith(":"):
                formatadas.append(linha)
            elif linha:
                formatadas.append(self.INDENT + linha)
            else:
                formatadas.append(linha)
        return "\n".join(formatadas)

    # ----- visitacao de comandos -----

    def _emit_cmd(self, cmd: Cmd) -> None:
        if isinstance(cmd, Atrib):
            self._emit(f"# {cmd.nome} = {cmd.exp};")
            self._emit_exp(cmd.exp)
            self._emit_armazena_variavel(cmd.nome)
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
            self._emit_carrega_variavel(no.nome)
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
        if isinstance(no, Chamada):
            self._emit_chamada(no)
            return
        raise TypeError(f"no de AST desconhecido: {type(no).__name__}")

    def _emit_carrega_variavel(self, nome: str) -> None:
        if self._quadro is not None and nome in self._quadro:
            self._emit(f"mov {self._quadro[nome]}(%rbp), %rax")
            return
        self._emit(f"mov {nome}, %rax")

    def _emit_armazena_variavel(self, nome: str) -> None:
        if self._quadro is not None and nome in self._quadro:
            self._emit(f"mov %rax, {self._quadro[nome]}(%rbp)")
            return
        self._emit(f"mov %rax, {nome}")

    def _emit_chamada(self, chamada: Chamada) -> None:
        # empilha os parametros em ordem inversa (ultimo primeiro),
        # para que o primeiro parametro fique mais proximo do topo
        # (mais perto do endereco de retorno) -- secao 6.1.1
        for arg in reversed(chamada.args):
            self._emit_exp(arg)
            self._emit("push %rax")
        self._emit(f"call {chamada.nome}")
        n_args = len(chamada.args)
        if n_args > 0:
            self._emit(f"add ${8 * n_args}, %rsp")

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
