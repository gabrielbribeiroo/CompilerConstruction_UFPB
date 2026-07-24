"""Analisador lexico para a linguagem Fun (funcoes).

Estende o lexer de Cmd (Atividade 09) com o unico token novo exigido
pela secao 3 do enunciado -- a virgula, usada para separar parametros
formais na declaracao de funcoes e parametros reais na chamada -- e
tres palavras-chave novas: fun, var e main.

O resto (numeros, identificadores, operadores aritmeticos e de
comparacao, pontuacao, if/else/while/return) e identico a Atividade 09.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TipoToken(Enum):
    NUMERO = auto()
    IDENT = auto()
    PALAVRA_IF = auto()
    PALAVRA_ELSE = auto()
    PALAVRA_WHILE = auto()
    PALAVRA_RETURN = auto()
    PALAVRA_FUN = auto()
    PALAVRA_VAR = auto()
    PALAVRA_MAIN = auto()
    PAREN_ESQ = auto()
    PAREN_DIR = auto()
    CHAVE_ESQ = auto()
    CHAVE_DIR = auto()
    VIRGULA = auto()
    SOMA = auto()
    SUB = auto()
    MULT = auto()
    DIV = auto()
    MENOR = auto()
    MAIOR = auto()
    IGUAL = auto()
    IGUAL_IGUAL = auto()
    PONTO_VIRGULA = auto()
    EOF = auto()


NOME_TOKEN = {
    TipoToken.NUMERO: "Numero",
    TipoToken.IDENT: "Ident",
    TipoToken.PALAVRA_IF: "If",
    TipoToken.PALAVRA_ELSE: "Else",
    TipoToken.PALAVRA_WHILE: "While",
    TipoToken.PALAVRA_RETURN: "Return",
    TipoToken.PALAVRA_FUN: "Fun",
    TipoToken.PALAVRA_VAR: "Var",
    TipoToken.PALAVRA_MAIN: "Main",
    TipoToken.PAREN_ESQ: "ParenEsq",
    TipoToken.PAREN_DIR: "ParenDir",
    TipoToken.CHAVE_ESQ: "ChaveEsq",
    TipoToken.CHAVE_DIR: "ChaveDir",
    TipoToken.VIRGULA: "Virgula",
    TipoToken.SOMA: "Soma",
    TipoToken.SUB: "Sub",
    TipoToken.MULT: "Mult",
    TipoToken.DIV: "Div",
    TipoToken.MENOR: "Menor",
    TipoToken.MAIOR: "Maior",
    TipoToken.IGUAL: "Igual",
    TipoToken.IGUAL_IGUAL: "IgualIgual",
    TipoToken.PONTO_VIRGULA: "PontoVirgula",
    TipoToken.EOF: "EOF",
}


PALAVRAS_CHAVE = {
    "if": TipoToken.PALAVRA_IF,
    "else": TipoToken.PALAVRA_ELSE,
    "while": TipoToken.PALAVRA_WHILE,
    "return": TipoToken.PALAVRA_RETURN,
    "fun": TipoToken.PALAVRA_FUN,
    "var": TipoToken.PALAVRA_VAR,
    "main": TipoToken.PALAVRA_MAIN,
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
    "{": TipoToken.CHAVE_ESQ,
    "}": TipoToken.CHAVE_DIR,
    ",": TipoToken.VIRGULA,
    "+": TipoToken.SOMA,
    "-": TipoToken.SUB,
    "*": TipoToken.MULT,
    "/": TipoToken.DIV,
    "<": TipoToken.MENOR,
    ">": TipoToken.MAIOR,
    ";": TipoToken.PONTO_VIRGULA,
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
        if c.isalpha():
            return self._ler_identificador_ou_palavra_chave()
        if c == "=":
            return self._ler_igual()
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
        # digitos seguidos imediatamente de uma letra, sem separador,
        # continuam sendo erro lexico (mesma regra desde a Atividade 08)
        if self._pos < len(self._fonte) and self._fonte[self._pos].isalpha():
            raise ErroLexico(self._pos, self._fonte[self._pos])
        return Token(TipoToken.NUMERO, self._fonte[inicio:self._pos], inicio)

    def _ler_identificador_ou_palavra_chave(self) -> Token:
        inicio = self._pos
        self._pos += 1  # primeira letra ja confirmada pelo chamador
        while self._pos < len(self._fonte) and self._fonte[self._pos].isalnum():
            self._pos += 1
        lexema = self._fonte[inicio:self._pos]
        tipo = PALAVRAS_CHAVE.get(lexema, TipoToken.IDENT)
        return Token(tipo, lexema, inicio)

    def _ler_igual(self) -> Token:
        inicio = self._pos
        # o caractere em self._pos e '=' (confirmado pelo chamador)
        if self._pos + 1 < len(self._fonte) and self._fonte[self._pos + 1] == "=":
            self._pos += 2
            return Token(TipoToken.IGUAL_IGUAL, "==", inicio)
        self._pos += 1
        return Token(TipoToken.IGUAL, "=", inicio)


__all__ = [
    "TipoToken",
    "Token",
    "ErroLexico",
    "AnalisadorLexico",
    "NOME_TOKEN",
    "PALAVRAS_CHAVE",
]
