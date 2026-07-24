"""Analise semantica (contextual) para a linguagem Fun.

Estende a verificacao de variaveis das Atividades 08/09 com as
verificacoes exigidas pela secao 5 do enunciado:

    5.1. Verificacao de chamadas de funcao -- a funcao chamada precisa
         ter sido declarada, e o numero de parametros reais precisa
         bater com o numero de parametros formais.
    5.2. Verificacao de variaveis usadas em funcoes -- dentro do corpo
         de uma funcao, uma variavel local (parametro ou `var` local)
         tem precedencia sobre uma global de mesmo nome.

A tabela de simbolos tem dois namespaces: variaveis globais e funcoes
(cada uma com sua aridade). Cada funcao, ao ser verificada, usa um
conjunto proprio de nomes locais (paramentros + var locais, na ordem
declarada) que e consultado ANTES do namespace global.

Declaracoes sao processadas sequencialmente (na ordem do
codigo-fonte). Uma funcao e registrada na tabela ANTES de seu proprio
corpo ser verificado -- isso e o que permite chamadas diretamente
recursivas (ex.: fib chamando fib) sem que o compilador rejeite a
chamada por "funcao ainda nao declarada". Como consequencia esperada
(nao um bug), funcoes MUTUAMENTE recursivas nao sao aceitas, pois uma
funcao so pode chamar outras ja declaradas antes dela no texto (ou a
si mesma).
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
    OpBin,
    Programa,
    Var,
    VarDecl,
    While,
)


class ErroSemantico(Exception):
    """Levantada para qualquer violacao das regras semanticas de Fun:
    uso de variavel/funcao nao declarada, atribuicao a nome nao
    declarado, numero de parametros incorreto em uma chamada, ou uso
    de um nome com o tipo de entidade errado (variavel vs. funcao)."""

    def __init__(self, mensagem: str, posicao: int) -> None:
        self.posicao = posicao
        super().__init__(f"Erro semantico na posicao {posicao}: {mensagem}")


class TabelaSimbolos:
    """Guarda os dois namespaces de nomes do programa: variaveis
    globais e funcoes declaradas (com sua aridade). Nao ha necessidade
    de guardar mais informacao (tipo, por exemplo), pois todos os
    valores em Fun sao inteiros."""

    def __init__(self) -> None:
        self._vars_globais: set[str] = set()
        self._funcoes: dict[str, int] = {}  # nome -> numero de parametros

    def declarar_var_global(self, nome: str) -> None:
        self._vars_globais.add(nome)

    def declarar_funcao(self, nome: str, n_parametros: int) -> None:
        self._funcoes[nome] = n_parametros

    def var_global_declarada(self, nome: str) -> bool:
        return nome in self._vars_globais

    def funcao_declarada(self, nome: str) -> bool:
        return nome in self._funcoes

    def n_parametros(self, nome: str) -> int:
        return self._funcoes[nome]


def _verifica_exp(exp: Exp, tabela: TabelaSimbolos, locais: set[str] | None) -> None:
    """`locais` e None fora de qualquer funcao (contexto global/main),
    ou o conjunto de nomes locais (parametros + var locais ja
    declaradas ate aqui) quando dentro do corpo de uma funcao."""
    if isinstance(exp, Const):
        return
    if isinstance(exp, Var):
        if locais is not None and exp.nome in locais:
            return
        if tabela.var_global_declarada(exp.nome):
            return
        if tabela.funcao_declarada(exp.nome):
            raise ErroSemantico(
                f"{exp.nome!r} é uma função, não uma variável", exp.posicao
            )
        raise ErroSemantico(
            f"variável {exp.nome!r} usada antes de ser declarada", exp.posicao
        )
    if isinstance(exp, OpBin):
        _verifica_exp(exp.esq, tabela, locais)
        _verifica_exp(exp.dir, tabela, locais)
        return
    if isinstance(exp, Chamada):
        if not tabela.funcao_declarada(exp.nome):
            eh_variavel = tabela.var_global_declarada(exp.nome) or (
                locais is not None and exp.nome in locais
            )
            if eh_variavel:
                raise ErroSemantico(
                    f"{exp.nome!r} é uma variável, não uma função", exp.posicao
                )
            raise ErroSemantico(
                f"função {exp.nome!r} usada antes de ser declarada", exp.posicao
            )
        esperado = tabela.n_parametros(exp.nome)
        obtido = len(exp.args)
        if obtido != esperado:
            raise ErroSemantico(
                f"função {exp.nome!r} espera {esperado} parâmetro(s), "
                f"recebeu {obtido}",
                exp.posicao,
            )
        for arg in exp.args:
            _verifica_exp(arg, tabela, locais)
        return
    raise TypeError(f"no de expressao desconhecido: {type(exp).__name__}")


def _verifica_cmd(cmd: Cmd, tabela: TabelaSimbolos, locais: set[str] | None) -> None:
    if isinstance(cmd, Atrib):
        # lado direito primeiro (ordem natural de execucao), depois o
        # lado esquerdo -- nenhum dos dois pode referenciar/ser um
        # nome nao declarado, e a atribuicao nao insere nada na tabela
        _verifica_exp(cmd.exp, tabela, locais)
        eh_variavel_declarada = (locais is not None and cmd.nome in locais) or (
            tabela.var_global_declarada(cmd.nome)
        )
        if not eh_variavel_declarada:
            if tabela.funcao_declarada(cmd.nome):
                raise ErroSemantico(
                    f"{cmd.nome!r} é uma função, não pode receber atribuição",
                    cmd.posicao,
                )
            raise ErroSemantico(
                f"variável {cmd.nome!r} usada antes de ser declarada", cmd.posicao
            )
        return
    if isinstance(cmd, If):
        _verifica_exp(cmd.cond, tabela, locais)
        for c in cmd.cmds_then:
            _verifica_cmd(c, tabela, locais)
        for c in cmd.cmds_else:
            _verifica_cmd(c, tabela, locais)
        return
    if isinstance(cmd, While):
        _verifica_exp(cmd.cond, tabela, locais)
        for c in cmd.cmds:
            _verifica_cmd(c, tabela, locais)
        return
    raise TypeError(f"no de comando desconhecido: {type(cmd).__name__}")


def _verifica_fundecl(fundecl: FunDecl, tabela: TabelaSimbolos) -> None:
    """Verifica o corpo de uma funcao. Pressupoe que `fundecl.nome` ja
    foi registrado em `tabela` (permitindo recursao direta)."""
    locais: set[str] = set(fundecl.params)
    for vd in fundecl.vardecls:
        _verifica_exp(vd.exp, tabela, locais)
        locais.add(vd.nome)
    for cmd in fundecl.comandos:
        _verifica_cmd(cmd, tabela, locais)
    _verifica_exp(fundecl.exp_final, tabela, locais)


def verifica_programa(programa: Programa) -> TabelaSimbolos:
    """Verifica todo o programa: declaracoes globais e de funcao (na
    ordem em que aparecem), depois o bloco main.

    Levanta ErroSemantico no primeiro problema encontrado. Devolve a
    tabela de simbolos final (util para depuracao/testes).
    """
    tabela = TabelaSimbolos()
    for decl in programa.declaracoes:
        if isinstance(decl, VarDecl):
            _verifica_exp(decl.exp, tabela, None)
            tabela.declarar_var_global(decl.nome)
        elif isinstance(decl, FunDecl):
            # registra a funcao ANTES de verificar seu proprio corpo,
            # para permitir chamadas diretamente recursivas
            tabela.declarar_funcao(decl.nome, len(decl.params))
            _verifica_fundecl(decl, tabela)
        else:
            raise TypeError(f"declaracao desconhecida: {type(decl).__name__}")
    for cmd in programa.comandos:
        _verifica_cmd(cmd, tabela, None)
    _verifica_exp(programa.exp_final, tabela, None)
    return tabela


__all__ = ["ErroSemantico", "TabelaSimbolos", "verifica_programa"]
