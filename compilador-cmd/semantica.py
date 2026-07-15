"""Analise semantica (contextual) para a linguagem Cmd.

Estende a verificacao de variaveis da Atividade 08 (EV) para lidar com
comandos: If, While e Atrib. A unica verificacao nova exigida pela
secao 5 do enunciado e a do comando de atribuicao, que tem dois
componentes a checar:

    - o lado direito (a expressao com o novo valor) nao pode
      referenciar nenhuma variavel nao declarada;
    - o lado esquerdo (a variavel que recebe o valor) tambem precisa
      ja estar declarada -- a atribuicao NAO cria variaveis novas.

Comandos If/While sao percorridos recursivamente (a condicao e cada
bloco de comandos), sem qualquer efeito na tabela de simbolos alem do
que a propria verificacao de variaveis dentro deles produzir.
"""

from __future__ import annotations

from ast_cmd import Atrib, Cmd, Const, Exp, If, OpBin, Programa, Var, While


class ErroSemantico(Exception):
    """Levantada quando uma variavel e usada (ou atribuida) antes de
    ser declarada."""

    def __init__(self, nome: str, posicao: int) -> None:
        self.nome = nome
        self.posicao = posicao
        super().__init__(
            f"Erro semantico na posicao {posicao}: variavel {nome!r} "
            f"usada antes de ser declarada"
        )


class TabelaSimbolos:
    """Guarda quais nomes de variavel ja foram declarados.

    Para a linguagem Cmd (como em EV) so precisamos saber SE a
    variavel foi declarada -- nao ha necessidade de guardar tipo,
    escopo ou qualquer outra informacao adicional.
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


def _verifica_cmd(cmd: Cmd, tabela: TabelaSimbolos) -> None:
    if isinstance(cmd, Atrib):
        # lado direito primeiro (ordem natural de execucao: calcula o
        # valor antes de guardar), depois o lado esquerdo -- nenhum
        # dos dois pode referenciar/ser uma variavel nao declarada, e
        # a atribuicao nao insere nada na tabela de simbolos.
        _verifica_exp(cmd.exp, tabela)
        if not tabela.esta_declarada(cmd.nome):
            raise ErroSemantico(cmd.nome, cmd.posicao)
        return
    if isinstance(cmd, If):
        _verifica_exp(cmd.cond, tabela)
        for c in cmd.cmds_then:
            _verifica_cmd(c, tabela)
        for c in cmd.cmds_else:
            _verifica_cmd(c, tabela)
        return
    if isinstance(cmd, While):
        _verifica_exp(cmd.cond, tabela)
        for c in cmd.cmds:
            _verifica_cmd(c, tabela)
        return
    raise TypeError(f"no de comando desconhecido: {type(cmd).__name__}")


def verifica_programa(programa: Programa) -> TabelaSimbolos:
    """Verifica todas as referencias e atribuicoes de variaveis do programa.

    Levanta ErroSemantico no primeiro uso (ou atribuicao) de variavel
    nao declarada. Devolve a tabela de simbolos final (util para
    depuracao/testes).
    """
    tabela = TabelaSimbolos()
    for decl in programa.declaracoes:
        _verifica_exp(decl.exp, tabela)
        tabela.declarar(decl.nome)
    for cmd in programa.comandos:
        _verifica_cmd(cmd, tabela)
    _verifica_exp(programa.exp_final, tabela)
    return tabela


__all__ = ["ErroSemantico", "TabelaSimbolos", "verifica_programa"]
