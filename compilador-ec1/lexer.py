"""Analisador lexico para a linguagem EC1.

Reusa a mesma estrutura da Atividade 04 (Analise Lexica EC1). Fornece duas
interfaces ao parser:
    - proximo_token() consome e retorna o proximo token;
    - olhar_proximo() retorna o proximo token sem consumir.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TipoToken(Enum):
    NUMERO = auto()
    PAREN_ESQ = auto()
    PAREN_DIR = auto()
    SOMA = auto()
    SUB = auto()
    MULT = auto()
    DIV = auto()
    EOF = auto()


# mapeamento usado na impressao no formato do enunciado
NOME_TOKEN = {
    TipoToken.NUMERO: "Numero",
    TipoToken.PAREN_ESQ: "ParenEsq",
    TipoToken.PAREN_DIR: "ParenDir",
    TipoToken.SOMA: "Soma",
    TipoToken.SUB: "Sub",
    TipoToken.MULT: "Mult",
    TipoToken.DIV: "Div",
    TipoToken.EOF: "EOF",
}


@dataclass(frozen=True)
class Token:
    tipo: TipoToken
    lexema: str
    posicao: int

    def __str__(self) -> str:
        return f'<{NOME_TOKEN[self.tipo]}, "{self.lexema}", {self.posicao}>'


class ErroLexico(Exception):
    def __init__(self, posicao: int, caractere: str) -> None:
        self.posicao = posicao
        self.caractere = caractere
        super().__init__(
            f"Erro lexico na posicao {posicao}: caractere inesperado "
            f"{caractere!r} (ASCII {ord(caractere)})"
        )


ESPACOS = frozenset({" ", "\t", "\n", "\r"})
CHAR_SIMPLES = {
    "(": TipoToken.PAREN_ESQ,
    ")": TipoToken.PAREN_DIR,
    "+": TipoToken.SOMA,
    "-": TipoToken.SUB,
    "*": TipoToken.MULT,
    "/": TipoToken.DIV,
}


class AnalisadorLexico:
    """Analisador lexico com lookahead de 1 token."""

    def __init__(self, fonte: str) -> None:
        self._fonte = fonte
        self._pos = 0
        self._buffer: Token | None = None  # token "olhado" sem consumir

    # ----- API publica -----

    def proximo_token(self) -> Token:
        """Consome e retorna o proximo token, ou EOF se a entrada acabou."""
        if self._buffer is not None:
            tok = self._buffer
            self._buffer = None
            return tok
        return self._gerar_proximo()

    def olhar_proximo(self) -> Token:
        """Retorna o proximo token sem consumir."""
        if self._buffer is None:
            self._buffer = self._gerar_proximo()
        return self._buffer

    def tokenizar(self) -> list[Token]:
        """Varre toda a entrada e devolve a lista de tokens (sem EOF)."""
        tokens: list[Token] = []
        while True:
            tok = self.proximo_token()
            if tok.tipo == TipoToken.EOF:
                break
            tokens.append(tok)
        return tokens

    # ----- internos -----

    def _gerar_proximo(self) -> Token:
        self._pular_brancos_e_comentarios()
        if self._pos >= len(self._fonte):
            return Token(TipoToken.EOF, "", self._pos)

        c = self._fonte[self._pos]
        if c.isdigit():
            return self._ler_numero()
        if c in CHAR_SIMPLES:
            tok = Token(CHAR_SIMPLES[c], c, self._pos)
            self._pos += 1
            return tok
        raise ErroLexico(self._pos, c)

    def _pular_brancos_e_comentarios(self) -> None:
        while self._pos < len(self._fonte):
            c = self._fonte[self._pos]
            if c in ESPACOS:
                self._pos += 1
            elif c == "#":
                # comentario de linha: descarta ate \n ou fim do arquivo
                while self._pos < len(self._fonte) and self._fonte[self._pos] != "\n":
                    self._pos += 1
            else:
                break

    def _ler_numero(self) -> Token:
        inicio = self._pos
        while self._pos < len(self._fonte) and self._fonte[self._pos].isdigit():
            self._pos += 1
        return Token(TipoToken.NUMERO, self._fonte[inicio:self._pos], inicio)


__all__ = [
    "TipoToken",
    "Token",
    "ErroLexico",
    "AnalisadorLexico",
    "NOME_TOKEN",
]
