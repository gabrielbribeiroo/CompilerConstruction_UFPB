"""Arvore de Sintaxe Abstrata para a linguagem EV (Expressoes com Variaveis).

Reaproveita a base ja usada desde a Atividade 05 (Exp, Const, OpBin, Op)
e adiciona os nos exigidos pela linguagem EV:

    Exp (abstrata)
      |- Const     valor inteiro
      |- Var       referencia a uma variavel (nome)
      |- OpBin     op, esq, dir

    Decl          declaracao: nome = exp;  (nao e uma Exp)
    Programa      no raiz: lista de Decl + expressao final

O metodo avaliar(env) em cada classe implementa um interpretador por
varredura da arvore, agora recebendo um ambiente (dict nome -> valor)
para poder resolver referencias a variaveis.

O metodo __str__() reconstroi a expressao/declaracao em uma forma
textual proxima da sintaxe concreta, util para depuracao e testes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Op(Enum):
    """Os quatro operadores binarios da linguagem EV."""

    SOMA = "+"
    SUB = "-"
    MULT = "*"
    DIV = "/"


class Exp:
    """Classe-base abstrata para nos de expressao da AST de EV."""

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
    """No-folha: uma referencia a uma variavel.

    ``posicao`` guarda o indice do identificador no texto-fonte, usado
    para mensagens de erro semantico; nao participa da igualdade entre
    nos (compare=False), para que os testes de estrutura da AST possam
    comparar `Var("x")` sem precisar repetir a posicao exata.
    """

    nome: str
    posicao: int = field(default=-1, compare=False)

    def avaliar(self, env: dict[str, int]) -> int:
        return env[self.nome]

    def __str__(self) -> str:
        return self.nome


@dataclass(frozen=True)
class OpBin(Exp):
    """No-interno: uma operacao binaria com dois sub-nos."""

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
        raise RuntimeError(f"operador desconhecido: {self.op}")

    def _erro_divisao_zero(self) -> int:
        raise ZeroDivisionError("divisao por zero durante a interpretacao")

    def __str__(self) -> str:
        return f"({self.esq} {self.op.value} {self.dir})"


@dataclass(frozen=True)
class Decl:
    """Uma declaracao de variavel: `nome = exp;`. Nao e uma Exp."""

    nome: str
    exp: Exp

    def __str__(self) -> str:
        return f"{self.nome} = {self.exp};"


@dataclass(frozen=True)
class Programa:
    """No raiz da AST de EV: zero ou mais declaracoes + expressao final."""

    declaracoes: tuple[Decl, ...]
    exp_final: Exp

    def avaliar(self) -> int:
        """Executa o programa inteiro e devolve o valor da expressao final."""
        env: dict[str, int] = {}
        for decl in self.declaracoes:
            env[decl.nome] = decl.exp.avaliar(env)
        return self.exp_final.avaliar(env)

    def __str__(self) -> str:
        linhas = [str(d) for d in self.declaracoes]
        linhas.append(f"= {self.exp_final}")
        return "\n".join(linhas)


__all__ = ["Exp", "Const", "Var", "OpBin", "Op", "Decl", "Programa"]
