"""Analisador sintatico descendente recursivo para a linguagem EC1.

Implementacao direta do pseudo-codigo do enunciado (secoes 3 e 6), com uma
funcao por nao-terminal:

    <programa>  ::= <expressao>
    <expressao> ::= <literal>
                  | '(' <expressao> <operador> <expressao> ')'
    <operador>  ::= '+' | '-' | '*' | '/'

Producao: uma arvore de sintaxe abstrata (Exp) que pode ser interpretada
diretamente via metodo avaliar().
"""

from __future__ import annotations

from ast_ec1 import Const, Exp, Op, OpBin
from lexer import AnalisadorLexico, NOME_TOKEN, TipoToken, Token


# operadores reconhecidos e o Op correspondente na AST
_OPERADORES: dict[TipoToken, Op] = {
    TipoToken.SOMA: Op.SOMA,
    TipoToken.SUB: Op.SUB,
    TipoToken.MULT: Op.MULT,
    TipoToken.DIV: Op.DIV,
}


class ErroSintatico(Exception):
    """Levantada quando a sequencia de tokens nao segue a gramatica EC1."""

    def __init__(self, mensagem: str, posicao: int) -> None:
        self.posicao = posicao
        super().__init__(f"Erro sintatico na posicao {posicao}: {mensagem}")


class AnalisadorSintatico:
    """Constroi a arvore sintatica de uma fonte EC1."""

    def __init__(self, fonte: str) -> None:
        self._lex = AnalisadorLexico(fonte)

    def analisa_programa(self) -> Exp:
        """Reconhece <programa>, garantindo que a entrada termina apos a expressao."""
        arvore = self._analisa_exp()
        prox = self._lex.proximo_token()
        if prox.tipo != TipoToken.EOF:
            raise ErroSintatico(
                f"esperado fim da entrada, encontrado {self._descreve(prox)}",
                prox.posicao,
            )
        return arvore

    # ----- nao-terminais -----

    def _analisa_exp(self) -> Exp:
        tok = self._lex.proximo_token()
        if tok.tipo == TipoToken.NUMERO:
            return Const(int(tok.lexema))
        if tok.tipo == TipoToken.PAREN_ESQ:
            esq = self._analisa_exp()
            op = self._analisa_operador()
            dir_ = self._analisa_exp()
            self._verifica_token(TipoToken.PAREN_DIR)
            return OpBin(op, esq, dir_)
        if tok.tipo == TipoToken.EOF:
            raise ErroSintatico(
                "esperado um literal inteiro ou '(', encontrado fim da entrada",
                tok.posicao,
            )
        raise ErroSintatico(
            f"esperado um literal inteiro ou '(', encontrado {self._descreve(tok)}",
            tok.posicao,
        )

    def _analisa_operador(self) -> Op:
        tok = self._lex.proximo_token()
        if tok.tipo in _OPERADORES:
            return _OPERADORES[tok.tipo]
        raise ErroSintatico(
            f"esperado um operador ('+', '-', '*' ou '/'), "
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


def analisar(fonte: str) -> Exp:
    """Atalho funcional: recebe a string e devolve a arvore sintatica."""
    return AnalisadorSintatico(fonte).analisa_programa()


__all__ = ["AnalisadorSintatico", "ErroSintatico", "analisar"]
