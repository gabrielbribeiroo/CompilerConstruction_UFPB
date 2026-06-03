"""Arvore de Sintaxe Abstrata para a linguagem EC1.

Segue a hierarquia sugerida no enunciado (secao 5):
    Exp (abstrata)
      |- Const     valor inteiro
      |- OpBin     op, esq, dir

O metodo avaliar() em cada classe implementa o interpretador por varredura
da arvore (secao 8).

O metodo __str__() reconstroi a expressao no formato canonico do enunciado
(secao 9, "impressao simples"), util para testes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Op(Enum):
    """Os quatro operadores binarios da linguagem EC1."""

    SOMA = "+"
    SUB = "-"
    MULT = "*"
    DIV = "/"


class Exp:
    """Classe-base abstrata para nos da arvore sintatica de EC1."""

    def avaliar(self) -> int:
        raise NotImplementedError("subclasse deve implementar avaliar()")

    def __str__(self) -> str:
        raise NotImplementedError("subclasse deve implementar __str__()")


@dataclass(frozen=True)
class Const(Exp):
    """No-folha: uma constante inteira."""

    valor: int

    def avaliar(self) -> int:
        return self.valor

    def __str__(self) -> str:
        return str(self.valor)


@dataclass(frozen=True)
class OpBin(Exp):
    """No-interno: uma operacao binaria com dois sub-nos."""

    op: Op
    esq: Exp
    dir: Exp

    def avaliar(self) -> int:
        ve = self.esq.avaliar()
        vd = self.dir.avaliar()
        if self.op is Op.SOMA:
            return ve + vd
        if self.op is Op.SUB:
            return ve - vd
        if self.op is Op.MULT:
            return ve * vd
        if self.op is Op.DIV:
            # divisao inteira (truncamento para zero) -- coerente com
            # operacoes inteiras em assembly, alvo da disciplina
            return int(ve / vd) if vd != 0 else self._erro_divisao_zero()
        raise RuntimeError(f"operador desconhecido: {self.op}")

    def _erro_divisao_zero(self) -> int:
        raise ZeroDivisionError("divisao por zero durante a interpretacao")

    def __str__(self) -> str:
        return f"({self.esq} {self.op.value} {self.dir})"


__all__ = ["Exp", "Const", "OpBin", "Op"]
