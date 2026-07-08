"""Analisador sintatico descendente recursivo para a linguagem EV.

Gramatica (secao 2 e 4 do enunciado):

    <programa> ::= <decl>* <result>
    <decl>     ::= <ident> '=' <exp> ';'
    <result>   ::= '=' <exp>
    <exp>      ::= <exp_m> (('+' | '-') <exp_m>)*
    <exp_m>    ::= <prim> (('*' | '/') <prim>)*
    <prim>     ::= <num> | <ident> | '(' <exp> ')'

A parte de expressoes (exp/exp_m/prim) e a mesma tecnica das Atividades
06/07 -- um nao-terminal por nivel de precedencia, com laco para as
producoes repetidas -- estendida apenas em `prim`, que agora tambem
reconhece um identificador como referencia a variavel (Var).

`analisa_programa()` segue o pseudocodigo da secao 4: olha o proximo
token e, enquanto for um identificador, reconhece uma declaracao;
quando encontrar '=', reconhece a expressao final e monta o no raiz
Programa.
"""

from __future__ import annotations

from ast_ev import Const, Decl, Exp, Op, OpBin, Programa, Var
from lexer import AnalisadorLexico, NOME_TOKEN, TipoToken, Token


_OPERADORES_ADITIVOS: dict[TipoToken, Op] = {
    TipoToken.SOMA: Op.SOMA,
    TipoToken.SUB: Op.SUB,
}

_OPERADORES_MULTIPLICATIVOS: dict[TipoToken, Op] = {
    TipoToken.MULT: Op.MULT,
    TipoToken.DIV: Op.DIV,
}


class ErroSintatico(Exception):
    """Levantada quando a sequencia de tokens nao segue a gramatica EV."""

    def __init__(self, mensagem: str, posicao: int) -> None:
        self.posicao = posicao
        super().__init__(f"Erro sintatico na posicao {posicao}: {mensagem}")


class AnalisadorSintatico:
    """Constroi a arvore sintatica de uma fonte EV."""

    def __init__(self, fonte: str) -> None:
        self._lex = AnalisadorLexico(fonte)

    # ----- <programa> ::= <decl>* <result> -----

    def analisa_programa(self) -> Programa:
        declaracoes: list[Decl] = []
        tok = self._lex.olhar_proximo()
        while tok.tipo == TipoToken.IDENT:
            declaracoes.append(self._analisa_decl())
            tok = self._lex.olhar_proximo()

        if tok.tipo != TipoToken.IGUAL:
            raise ErroSintatico(
                f"esperado '=' (inicio da expressao final) ou um identificador "
                f"(nova declaracao), encontrado {self._descreve(tok)}",
                tok.posicao,
            )
        self._lex.proximo_token()  # consome '='
        exp_final = self._analisa_exp_a()

        prox = self._lex.proximo_token()
        if prox.tipo != TipoToken.EOF:
            raise ErroSintatico(
                f"esperado fim da entrada, encontrado {self._descreve(prox)}",
                prox.posicao,
            )
        return Programa(tuple(declaracoes), exp_final)

    # ----- <decl> ::= <ident> '=' <exp> ';' -----

    def _analisa_decl(self) -> Decl:
        tok_ident = self._lex.proximo_token()  # ja sabemos que e IDENT
        self._verifica_token(TipoToken.IGUAL)
        exp = self._analisa_exp_a()
        self._verifica_token(TipoToken.PONTO_VIRGULA)
        return Decl(tok_ident.lexema, exp)

    # ----- <exp> ::= <exp_m> (('+' | '-') <exp_m>)* -----

    def _analisa_exp_a(self) -> Exp:
        esq = self._analisa_exp_m()
        tok = self._lex.olhar_proximo()
        while tok.tipo in _OPERADORES_ADITIVOS:
            self._lex.proximo_token()
            op = _OPERADORES_ADITIVOS[tok.tipo]
            dir_ = self._analisa_exp_m()
            esq = OpBin(op, esq, dir_)  # associatividade a esquerda
            tok = self._lex.olhar_proximo()
        return esq

    # ----- <exp_m> ::= <prim> (('*' | '/') <prim>)* -----

    def _analisa_exp_m(self) -> Exp:
        esq = self._analisa_prim()
        tok = self._lex.olhar_proximo()
        while tok.tipo in _OPERADORES_MULTIPLICATIVOS:
            self._lex.proximo_token()
            op = _OPERADORES_MULTIPLICATIVOS[tok.tipo]
            dir_ = self._analisa_prim()
            esq = OpBin(op, esq, dir_)  # associatividade a esquerda
            tok = self._lex.olhar_proximo()
        return esq

    # ----- <prim> ::= <num> | <ident> | '(' <exp> ')' -----

    def _analisa_prim(self) -> Exp:
        tok = self._lex.proximo_token()
        if tok.tipo == TipoToken.NUMERO:
            return Const(int(tok.lexema))
        if tok.tipo == TipoToken.IDENT:
            return Var(tok.lexema, tok.posicao)
        if tok.tipo == TipoToken.PAREN_ESQ:
            interna = self._analisa_exp_a()
            self._verifica_token(TipoToken.PAREN_DIR)
            return interna
        if tok.tipo == TipoToken.EOF:
            raise ErroSintatico(
                "esperado um literal inteiro, identificador ou '(', "
                "encontrado fim da entrada",
                tok.posicao,
            )
        raise ErroSintatico(
            f"esperado um literal inteiro, identificador ou '(', "
            f"encontrado {self._descreve(tok)}",
            tok.posicao,
        )

    # ----- utilidades -----

    def _verifica_token(self, tipo_esperado: TipoToken) -> Token:
        tok = self._lex.proximo_token()
        if tok.tipo != tipo_esperado:
            raise ErroSintatico(
                f"esperado {NOME_TOKEN[tipo_esperado]}, "
                f"encontrado {self._descreve(tok)}",
                tok.posicao,
            )
        return tok

    @staticmethod
    def _descreve(tok: Token) -> str:
        if tok.tipo == TipoToken.EOF:
            return "fim da entrada"
        return f"{NOME_TOKEN[tok.tipo]}({tok.lexema!r})"


def analisar(fonte: str) -> Programa:
    """Atalho funcional: recebe a string e devolve a arvore sintatica."""
    return AnalisadorSintatico(fonte).analisa_programa()


__all__ = ["AnalisadorSintatico", "ErroSintatico", "analisar"]
