"""Arvore de Sintaxe Abstrata para a linguagem Cmd (Atividade 09).

Reaproveita a base de expressoes ja usada desde a Atividade 05
(Exp, Const, Var, OpBin), estendendo Op com os tres operadores de
comparacao (MENOR, MAIOR, IGUAL), e adiciona os nos de comando
exigidos pela linguagem Cmd:

    Exp (abstrata)
      |- Const
      |- Var
      |- OpBin        agora tambem cobre comparacoes

    Cmd (abstrata)
      |- Atrib        nome = exp;
      |- If           if cond { ... } else { ... }
      |- While        while cond { ... }

    Decl             declaracao: nome = exp;  (nao e um Cmd)
    Programa         no raiz: declaracoes + comandos + expressao final

O metodo avaliar(env) em cada classe de Exp implementa o interpretador
por varredura da arvore (igual as atividades anteriores). A execucao
dos comandos e feita por _executar(), uma funcao recursiva que resolve
Atrib/If/While mutando o ambiente (dict) passado por referencia --
isso e o interpretador de referencia usado para validar a geracao de
codigo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Op(Enum):
    """Os operadores binarios da linguagem Cmd: aritmeticos e de comparacao."""

    SOMA = "+"
    SUB = "-"
    MULT = "*"
    DIV = "/"
    MENOR = "<"
    MAIOR = ">"
    IGUAL = "=="


class Exp:
    """Classe-base abstrata para nos de expressao da AST de Cmd."""

    def avaliar(self, env: dict[str, int]) -> int:
        raise NotImplementedError("subclasse deve implementar avaliar()")

    def __str__(self) -> str:
        raise NotImplementedError("subclasse deve implementar __str__()")


@dataclass(frozen=True)
class Const(Exp):
    """No-folha: uma constante inteira."""

    valor: int

    def avaliar(self, env: dict[str, int]) -> int:
        return self.valor

    def __str__(self) -> str:
        return str(self.valor)


@dataclass(frozen=True)
class Var(Exp):
    """No-folha: uma referencia a uma variavel."""

    nome: str
    posicao: int = field(default=-1, compare=False)

    def avaliar(self, env: dict[str, int]) -> int:
        return env[self.nome]

    def __str__(self) -> str:
        return self.nome


@dataclass(frozen=True)
class OpBin(Exp):
    """No-interno: uma operacao binaria (aritmetica ou de comparacao)."""

    op: Op
    esq: Exp
    dir: Exp

    def avaliar(self, env: dict[str, int]) -> int:
        ve = self.esq.avaliar(env)
        vd = self.dir.avaliar(env)
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
        raise RuntimeError(f"operador desconhecido: {self.op}")

    def _erro_divisao_zero(self) -> int:
        raise ZeroDivisionError("divisao por zero durante a interpretacao")

    def __str__(self) -> str:
        return f"({self.esq} {self.op.value} {self.dir})"


class Cmd:
    """Classe-base abstrata para nos de comando da AST de Cmd."""


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
class Decl:
    """Uma declaracao de variavel: `nome = exp;`. Nao e um Cmd nem uma Exp."""

    nome: str
    exp: Exp

    def __str__(self) -> str:
        return f"{self.nome} = {self.exp};"


@dataclass(frozen=True)
class Programa:
    """No raiz da AST de Cmd: declaracoes + comandos + expressao final."""

    declaracoes: tuple[Decl, ...]
    comandos: tuple[Cmd, ...]
    exp_final: Exp

    def avaliar(self) -> int:
        """Executa o programa inteiro e devolve o valor da expressao final."""
        env: dict[str, int] = {}
        for decl in self.declaracoes:
            env[decl.nome] = decl.exp.avaliar(env)
        _executar(self.comandos, env)
        return self.exp_final.avaliar(env)


def _executar(comandos: tuple[Cmd, ...], env: dict[str, int]) -> None:
    """Interpreta uma sequencia de comandos, mutando `env` conforme necessario."""
    for cmd in comandos:
        if isinstance(cmd, Atrib):
            env[cmd.nome] = cmd.exp.avaliar(env)
        elif isinstance(cmd, If):
            if cmd.cond.avaliar(env) != 0:
                _executar(cmd.cmds_then, env)
            else:
                _executar(cmd.cmds_else, env)
        elif isinstance(cmd, While):
            while cmd.cond.avaliar(env) != 0:
                _executar(cmd.cmds, env)
        else:
            raise TypeError(f"no de comando desconhecido: {type(cmd).__name__}")


__all__ = [
    "Exp",
    "Const",
    "Var",
    "OpBin",
    "Op",
    "Cmd",
    "Atrib",
    "If",
    "While",
    "Decl",
    "Programa",
]
