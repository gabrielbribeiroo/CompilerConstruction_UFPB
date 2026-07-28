"""Arvore de Sintaxe Abstrata para a linguagem Fun estendida (Projeto Final).

Reaproveita a AST da Atividade 10 (Exp, Const, Var, OpBin, Op,
Chamada, Cmd, Atrib, If, While, VarDecl, FunDecl, Programa) e
acrescenta o que as tres extensoes exigem:

    - `Op` ganha tres valores novos (MENOR_IGUAL, MAIOR_IGUAL,
      DIFERENTE) -- os operadores compostos de atribuicao (`+=` etc.)
      NAO exigem no novo nenhum: sao *acucar sintatico* desmontado
      pelo parser em um `Atrib` comum (`x += e` vira
      `Atrib(x, OpBin(SOMA, Var(x), e))`), reaproveitando toda a
      analise semantica e geracao de codigo de `Atrib` sem alteracao.
    - `Return(exp)` -- novo no de comando (`Cmd`), o comando `return`
      usado para saida antecipada de uma funcao/main a partir de
      dentro de um bloco aninhado (`if`/`while`).
    - `RetornoAntecipado` -- excecao interna usada por `_executar` e
      pelos pontos de avaliacao de corpo de funcao/main para
      implementar a semantica de `Return`: interrompe a execucao dos
      comandos remanescentes e devolve um valor imediatamente,
      exatamente como o `jmp` para o rotulo de saida faz no codigo
      gerado (ver codegen.py).

O interpretador de referencia (avaliar()) usa um Ambiente que separa
o escopo local (parametros + var locais da funcao em execucao) do
escopo global, com o local tendo precedencia -- exatamente a regra de
visibilidade da linguagem Fun (secao 2). Chamadas de funcao (inclusive
recursivas) criam um novo Ambiente com locais proprios a cada
ativacao, sem afetar o ambiente do chamador.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Op(Enum):
    """Os operadores binarios da linguagem Fun: aritmeticos e de comparacao."""

    SOMA = "+"
    SUB = "-"
    MULT = "*"
    DIV = "/"
    MENOR = "<"
    MAIOR = ">"
    IGUAL = "=="
    MENOR_IGUAL = "<="
    MAIOR_IGUAL = ">="
    DIFERENTE = "!="


class Exp:
    """Classe-base abstrata para nos de expressao da AST de Fun."""

    def avaliar(self, amb: "Ambiente") -> int:
        raise NotImplementedError("subclasse deve implementar avaliar()")

    def __str__(self) -> str:
        raise NotImplementedError("subclasse deve implementar __str__()")


@dataclass(frozen=True)
class Const(Exp):
    """No-folha: uma constante inteira."""

    valor: int

    def avaliar(self, amb: "Ambiente") -> int:
        return self.valor

    def __str__(self) -> str:
        return str(self.valor)


@dataclass(frozen=True)
class Var(Exp):
    """No-folha: uma referencia a uma variavel (local ou global)."""

    nome: str
    posicao: int = field(default=-1, compare=False)

    def avaliar(self, amb: "Ambiente") -> int:
        return amb.obter(self.nome)

    def __str__(self) -> str:
        return self.nome


@dataclass(frozen=True)
class OpBin(Exp):
    """No-interno: uma operacao binaria (aritmetica ou de comparacao)."""

    op: Op
    esq: Exp
    dir: Exp

    def avaliar(self, amb: "Ambiente") -> int:
        ve = self.esq.avaliar(amb)
        vd = self.dir.avaliar(amb)
        if self.op is Op.SOMA:
            return ve + vd
        if self.op is Op.SUB:
            return ve - vd
        if self.op is Op.MULT:
            return ve * vd
        if self.op is Op.DIV:
            return int(ve / vd) if vd != 0 else self._erro_divisao_zero()
        if self.op is Op.MENOR:
            return 1 if ve < vd else 0
        if self.op is Op.MAIOR:
            return 1 if ve > vd else 0
        if self.op is Op.IGUAL:
            return 1 if ve == vd else 0
        if self.op is Op.MENOR_IGUAL:
            return 1 if ve <= vd else 0
        if self.op is Op.MAIOR_IGUAL:
            return 1 if ve >= vd else 0
        if self.op is Op.DIFERENTE:
            return 1 if ve != vd else 0
        raise RuntimeError(f"operador desconhecido: {self.op}")

    def _erro_divisao_zero(self) -> int:
        raise ZeroDivisionError("divisao por zero durante a interpretacao")

    def __str__(self) -> str:
        return f"({self.esq} {self.op.value} {self.dir})"


@dataclass(frozen=True)
class Chamada(Exp):
    """No-interno: chamada de funcao, usada como expressao primaria."""

    nome: str
    args: tuple[Exp, ...]
    posicao: int = field(default=-1, compare=False)

    def avaliar(self, amb: "Ambiente") -> int:
        fundecl = amb.contexto.funcoes[self.nome]
        # os argumentos sao avaliados no ambiente do CHAMADOR, antes de
        # criar o novo escopo local da funcao chamada
        valores = [arg.avaliar(amb) for arg in self.args]
        locais = dict(zip(fundecl.params, valores))
        amb_fun = Ambiente(amb.contexto, locais)
        for vd in fundecl.vardecls:
            amb_fun.locais[vd.nome] = vd.exp.avaliar(amb_fun)
        try:
            _executar(fundecl.comandos, amb_fun)
        except RetornoAntecipado as retorno:
            return retorno.valor
        return fundecl.exp_final.avaliar(amb_fun)

    def __str__(self) -> str:
        return f"{self.nome}({', '.join(str(a) for a in self.args)})"


class Cmd:
    """Classe-base abstrata para nos de comando da AST de Fun."""


@dataclass(frozen=True)
class Atrib(Cmd):
    """Comando de atribuicao: `nome = exp;`. Nao cria variaveis novas."""

    nome: str
    exp: Exp
    posicao: int = field(default=-1, compare=False)

    def __str__(self) -> str:
        return f"{self.nome} = {self.exp};"


@dataclass(frozen=True)
class If(Cmd):
    """Comando condicional. O braco `else` e obrigatorio na gramatica
    (mas `cmds_else` pode ser uma tupla vazia)."""

    cond: Exp
    cmds_then: tuple[Cmd, ...]
    cmds_else: tuple[Cmd, ...]


@dataclass(frozen=True)
class While(Cmd):
    """Comando de repeticao."""

    cond: Exp
    cmds: tuple[Cmd, ...]


@dataclass(frozen=True)
class Return(Cmd):
    """Comando de retorno antecipado: `return exp;` usado dentro de um
    bloco aninhado (corpo de `if`/`while`), encerrando imediatamente a
    execucao da funcao ou do `main` corrente com o valor de `exp` --
    sem precisar propagar esse valor "na mao" ate o fim do corpo via
    variaveis auxiliares, como a linguagem Fun original exigia."""

    exp: Exp
    posicao: int = field(default=-1, compare=False)

    def __str__(self) -> str:
        return f"return {self.exp};"


class RetornoAntecipado(Exception):
    """Usada internamente por `_executar` e pelos avaliadores de corpo
    de funcao/main (`Chamada.avaliar`, `Programa.avaliar`) para
    implementar `Return`: interrompe a execucao da sequencia de
    comandos corrente (mesmo que aninhada dentro de varios niveis de
    `if`/`while`) e devolve `valor` como resultado da ativacao atual."""

    def __init__(self, valor: int) -> None:
        self.valor = valor


@dataclass(frozen=True)
class VarDecl:
    """Uma declaracao de variavel: `var nome = exp;`. Aparece tanto no
    nivel global do programa quanto (com outro significado de escopo)
    dentro do corpo de uma funcao."""

    nome: str
    exp: Exp

    def __str__(self) -> str:
        return f"var {self.nome} = {self.exp};"


@dataclass(frozen=True)
class FunDecl:
    """Declaracao de funcao: nome, parametros, variaveis locais
    proprias, comandos e expressao de resultado."""

    nome: str
    params: tuple[str, ...]
    vardecls: tuple[VarDecl, ...]
    comandos: tuple[Cmd, ...]
    exp_final: Exp


@dataclass(frozen=True)
class Programa:
    """No raiz da AST de Fun: declaracoes (VarDecl | FunDecl) + bloco main."""

    declaracoes: tuple["VarDecl | FunDecl", ...]
    comandos: tuple[Cmd, ...]
    exp_final: Exp

    def avaliar(self) -> int:
        """Executa o programa inteiro e devolve o valor da expressao final."""
        contexto = Contexto()
        for decl in self.declaracoes:
            if isinstance(decl, VarDecl):
                contexto.globais[decl.nome] = decl.exp.avaliar(Ambiente(contexto))
            elif isinstance(decl, FunDecl):
                contexto.funcoes[decl.nome] = decl
            else:
                raise TypeError(f"declaracao desconhecida: {type(decl).__name__}")
        amb_main = Ambiente(contexto)
        try:
            _executar(self.comandos, amb_main)
        except RetornoAntecipado as retorno:
            return retorno.valor
        return self.exp_final.avaliar(amb_main)


class Contexto:
    """Estado global compartilhado por todas as ativacoes de funcao
    durante a interpretacao: as variaveis globais e a tabela de
    funcoes declaradas (usada para resolver chamadas, inclusive
    recursivas)."""

    def __init__(self) -> None:
        self.globais: dict[str, int] = {}
        self.funcoes: dict[str, FunDecl] = {}


class Ambiente:
    """Escopo de avaliacao: um dicionario local (parametros + var
    locais da ativacao de funcao atual, vazio no bloco main) mais o
    contexto global. Uma referencia a variavel consulta primeiro o
    escopo local; se nao encontrar, cai para o global -- a regra de
    que uma variavel local esconde uma global de mesmo nome."""

    def __init__(self, contexto: Contexto, locais: dict[str, int] | None = None) -> None:
        self.contexto = contexto
        self.locais: dict[str, int] = locais if locais is not None else {}

    def obter(self, nome: str) -> int:
        if nome in self.locais:
            return self.locais[nome]
        return self.contexto.globais[nome]

    def definir(self, nome: str, valor: int) -> None:
        if nome in self.locais:
            self.locais[nome] = valor
        else:
            self.contexto.globais[nome] = valor


def _executar(comandos: tuple[Cmd, ...], amb: Ambiente) -> None:
    """Interpreta uma sequencia de comandos, mutando `amb` conforme necessario."""
    for cmd in comandos:
        if isinstance(cmd, Atrib):
            amb.definir(cmd.nome, cmd.exp.avaliar(amb))
        elif isinstance(cmd, If):
            if cmd.cond.avaliar(amb) != 0:
                _executar(cmd.cmds_then, amb)
            else:
                _executar(cmd.cmds_else, amb)
        elif isinstance(cmd, While):
            while cmd.cond.avaliar(amb) != 0:
                _executar(cmd.cmds, amb)
        elif isinstance(cmd, Return):
            # a excecao propaga naturalmente atraves de qualquer
            # aninhamento de if/while ate o try/except em
            # Chamada.avaliar/Programa.avaliar, interrompendo o
            # restante dos comandos (inclusive os de fora do
            # if/while onde o Return apareceu)
            raise RetornoAntecipado(cmd.exp.avaliar(amb))
        else:
            raise TypeError(f"no de comando desconhecido: {type(cmd).__name__}")


__all__ = [
    "Exp",
    "Const",
    "Var",
    "OpBin",
    "Op",
    "Chamada",
    "Cmd",
    "Atrib",
    "If",
    "While",
    "Return",
    "RetornoAntecipado",
    "VarDecl",
    "FunDecl",
    "Programa",
    "Contexto",
    "Ambiente",
]
