"""Analise semantica (contextual) para a linguagem EV.

Verifica que toda referencia a variavel usa um nome ja declarado antes
dela no programa-fonte -- o unico tipo de erro semantico que existe em
EV (secao 5 do enunciado; verificacao de tipos nao se aplica, pois
todas as variaveis tem o mesmo tipo).

O algoritmo percorre as declaracoes NA ORDEM em que aparecem no
codigo-fonte: para cada declaracao, verifica que as variaveis usadas na
expressao ja estao na tabela de simbolos; so entao declara a variavel
correspondente. Ao final, faz a mesma verificacao na expressao de
resultado. O processo para no primeiro erro encontrado.
"""

from __future__ import annotations

from ast_ev import Const, Exp, OpBin, Programa, Var


class ErroSemantico(Exception):
    """Levantada quando uma variavel e usada antes de ser declarada."""

    def __init__(self, nome: str, posicao: int) -> None:
        self.nome = nome
        self.posicao = posicao
        super().__init__(
            f"Erro semantico na posicao {posicao}: variavel {nome!r} "
            f"usada antes de ser declarada"
        )


class TabelaSimbolos:
    """Guarda quais nomes de variavel ja foram declarados.

    Para a linguagem EV so precisamos saber SE a variavel foi
    declarada -- nao ha necessidade de guardar tipo, escopo ou
    qualquer outra informacao adicional.
    """

    def __init__(self) -> None:
        self._declaradas: set[str] = set()

    def declarar(self, nome: str) -> None:
        self._declaradas.add(nome)

    def esta_declarada(self, nome: str) -> bool:
        return nome in self._declaradas


def _verifica_exp(exp: Exp, tabela: TabelaSimbolos) -> None:
    if isinstance(exp, Const):
        return
    if isinstance(exp, Var):
        if not tabela.esta_declarada(exp.nome):
            raise ErroSemantico(exp.nome, exp.posicao)
        return
    if isinstance(exp, OpBin):
        _verifica_exp(exp.esq, tabela)
        _verifica_exp(exp.dir, tabela)
        return
    raise TypeError(f"no de expressao desconhecido: {type(exp).__name__}")


def verifica_programa(programa: Programa) -> TabelaSimbolos:
    """Verifica todas as referencias a variaveis do programa.

    Levanta ErroSemantico no primeiro uso de variavel nao declarada.
    Devolve a tabela de simbolos final (util para depuracao/testes).
    """
    tabela = TabelaSimbolos()
    for decl in programa.declaracoes:
        _verifica_exp(decl.exp, tabela)
        tabela.declarar(decl.nome)
    _verifica_exp(programa.exp_final, tabela)
    return tabela


__all__ = ["ErroSemantico", "TabelaSimbolos", "verifica_programa"]
