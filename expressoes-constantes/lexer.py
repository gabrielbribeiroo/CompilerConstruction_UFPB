#!/usr/bin/env python3
"""Analisador lexico para a linguagem EC1 (Expressoes Constantes 1).

Uso:
    python lexer.py <arquivo_de_entrada>

Le um arquivo `.ec1`, varre a entrada caractere por caractere e imprime,
um por linha, cada token reconhecido no formato `<Tipo, "lexema", posicao>`.

Classes lexicas: numeros (sequencia de digitos), parenteses, os quatro
operadores aritmeticos, e o token EOF (fim da entrada). Espacos, tabs,
quebras de linha e retornos de carro sao descartados; comentarios de
linha iniciados por `#` (extensao opcional do enunciado) tambem sao
descartados, ate o fim da linha.

Em caso de erro lexico (caractere nao reconhecido), a mensagem vai para
stderr e o processo encerra com codigo de saida 1 -- nenhum token e
impresso apos o ponto do erro.
"""

from __future__ import annotations

import sys

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
            f"Erro léxico na posição {posicao}: caractere inesperado "
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
    """Analisador lexico: varre a entrada uma unica vez, da esquerda pra direita."""

    def __init__(self, fonte: str) -> None:
        self._fonte = fonte
        self._pos = 0

    # ----- API publica -----

    def proximo_token(self) -> Token:
        """Consome e retorna o proximo token, ou EOF se a entrada acabou."""
        return self._gerar_proximo()

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


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"uso: python {argv[0] or 'lexer.py'} <arquivo_de_entrada>", file=sys.stderr)
        return 2

    caminho_entrada = argv[1]
    try:
        with open(caminho_entrada, "r", encoding="utf-8") as f:
            fonte = f.read()
    except FileNotFoundError:
        print(f"erro: arquivo nao encontrado: {caminho_entrada}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"erro ao ler {caminho_entrada}: {exc}", file=sys.stderr)
        return 1

    try:
        tokens = AnalisadorLexico(fonte).tokenizar()
    except ErroLexico as exc:
        print(str(exc), file=sys.stderr)
        return 1

    for tok in tokens:
        print(tok)
    return 0


__all__ = [
    "TipoToken",
    "Token",
    "ErroLexico",
    "AnalisadorLexico",
    "NOME_TOKEN",
]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
