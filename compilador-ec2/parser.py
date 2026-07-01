"""Analisador sintatico descendente recursivo para a linguagem EC2.

EC2 estende EC1 (Atividade 04/05/06) permitindo expressoes com o minimo
de parenteses, respeitando as regras usuais de precedencia e
associatividade a esquerda. Gramatica (secao 3 do enunciado):

    <exp_a> ::= <exp_m> (('+' | '-') <exp_m>)*
    <exp_m> ::= <prim>  (('*' | '/') <prim>)*
    <prim>  ::= <num> | '(' <exp_a> ')'

exp_a e o nivel aditivo (precedencia mais baixa), exp_m e o nivel
multiplicativo (precedencia mais alta), e prim reconhece constantes ou
uma sub-expressao entre parenteses (que reinicia a analise em exp_a).

Cada producao com repeticao (o `(...)* `) vira um laco na funcao
correspondente, que usa "olhar_proximo" (peek) para decidir se continua
o laco sem consumir um token que nao pertence a essa producao. A cada
iteracao do laco, o no binario recem-criado vira o novo operando
esquerdo -- e e exatamente isso que da associatividade a esquerda.

Producao: uma arvore de sintaxe abstrata (Exp), a mesma hierarquia usada
desde a Atividade 05 -- Const e OpBin nao mudam, so a forma como sao
construidos.
"""

from __future__ import annotations

from ast_ec1 import Const, Exp, Op, OpBin
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
    """Levantada quando a sequencia de tokens nao segue a gramatica EC2."""

    def __init__(self, mensagem: str, posicao: int) -> None:
        self.posicao = posicao
        super().__init__(f"Erro sintatico na posicao {posicao}: {mensagem}")


class AnalisadorSintatico:
    """Constroi a arvore sintatica de uma fonte EC2."""

    def __init__(self, fonte: str) -> None:
        self._lex = AnalisadorLexico(fonte)

    def analisa_programa(self) -> Exp:
        """Reconhece o programa completo, exigindo EOF apos a expressao."""
        arvore = self._analisa_exp_a()
        prox = self._lex.proximo_token()
        if prox.tipo != TipoToken.EOF:
            raise ErroSintatico(
                f"esperado fim da entrada, encontrado {self._descreve(prox)}",
                prox.posicao,
            )
        return arvore

    # ----- nivel aditivo: <exp_a> ::= <exp_m> (('+' | '-') <exp_m>)* -----

    def _analisa_exp_a(self) -> Exp:
        esq = self._analisa_exp_m()
        tok = self._lex.olhar_proximo()
        while tok.tipo in _OPERADORES_ADITIVOS:
            self._lex.proximo_token()  # consome o operador
            op = _OPERADORES_ADITIVOS[tok.tipo]
            dir_ = self._analisa_exp_m()
            esq = OpBin(op, esq, dir_)  # associatividade a esquerda
            tok = self._lex.olhar_proximo()
        return esq

    # ----- nivel multiplicativo: <exp_m> ::= <prim> (('*' | '/') <prim>)* -----

    def _analisa_exp_m(self) -> Exp:
        esq = self._analisa_prim()
        tok = self._lex.olhar_proximo()
        while tok.tipo in _OPERADORES_MULTIPLICATIVOS:
            self._lex.proximo_token()  # consome o operador
            op = _OPERADORES_MULTIPLICATIVOS[tok.tipo]
            dir_ = self._analisa_prim()
            esq = OpBin(op, esq, dir_)  # associatividade a esquerda
            tok = self._lex.olhar_proximo()
        return esq

    # ----- expressao primaria: <prim> ::= <num> | '(' <exp_a> ')' -----

    def _analisa_prim(self) -> Exp:
        tok = self._lex.proximo_token()
        if tok.tipo == TipoToken.NUMERO:
            return Const(int(tok.lexema))
        if tok.tipo == TipoToken.PAREN_ESQ:
            interna = self._analisa_exp_a()
            self._verifica_token(TipoToken.PAREN_DIR)
            return interna
        if tok.tipo == TipoToken.EOF:
            raise ErroSintatico(
                "esperado um literal inteiro ou '(', encontrado fim da entrada",
                tok.posicao,
            )
        raise ErroSintatico(
            f"esperado um literal inteiro ou '(', encontrado {self._descreve(tok)}",
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
