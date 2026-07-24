"""Analisador sintatico descendente recursivo para a linguagem Fun.

Gramatica (secao 2.1 do enunciado):

    <programa> ::= <decl>* 'main' '{' <cmd>* 'return' <exp> ';' '}'
    <decl>     ::= <vardecl> | <fundecl>
    <fundecl>  ::= 'fun' <ident> '(' <arglist>? ')'
                   '{' <vardecl>* <cmd>* 'return' <exp> ';' '}'
    <arglist>  ::= <ident> | <ident> ',' <arglist>
    <vardecl>  ::= 'var' <ident> '=' <exp> ';'
    <cmd>      ::= <if> | <while> | <atrib>
    <if>       ::= 'if' <exp> '{' <cmd>* '}' 'else' '{' <cmd>* '}'
    <while>    ::= 'while' <exp> '{' <cmd>* '}'
    <atrib>    ::= <ident> '=' <exp> ';'
    <exp>      ::= <exp_a> (('<' | '>' | '==') <exp_a>)*
    <exp_a>    ::= <exp_m> (('+' | '-') <exp_m>)*
    <exp_m>    ::= <prim> (('*' | '/') <prim>)*
    <prim>     ::= <num> | <ident> | '(' <exp> ')' | <fun>
    <fun>      ::= <ident> '(' <params>? ')'
    <params>   ::= <exp> | <exp> ',' <params>

A parte de expressoes aritmeticas/comparacao (exp/exp_a/exp_m) e a
mesma tecnica das Atividades 07-09. A novidade estrutural (secao 4 do
enunciado):

    - `decl` escolhe entre vardecl/fundecl por peek na palavra-chave
      ('var' ou 'fun');
    - listas de parametros (formais em fundecl, reais em Chamada) sao
      reconhecidas em um laco que olha o proximo token ate encontrar
      ')', tratando a virgula como separador;
    - `prim` decide entre Var e Chamada olhando o token IMEDIATAMENTE
      apos um identificador: se for '(', e uma chamada de funcao;
      caso contrario, e uma referencia a variavel.
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
    Op,
    OpBin,
    Programa,
    Var,
    VarDecl,
    While,
)
from lexer import AnalisadorLexico, NOME_TOKEN, TipoToken, Token


_OPERADORES_ADITIVOS: dict[TipoToken, Op] = {
    TipoToken.SOMA: Op.SOMA,
    TipoToken.SUB: Op.SUB,
}

_OPERADORES_MULTIPLICATIVOS: dict[TipoToken, Op] = {
    TipoToken.MULT: Op.MULT,
    TipoToken.DIV: Op.DIV,
}

_OPERADORES_COMPARACAO: dict[TipoToken, Op] = {
    TipoToken.MENOR: Op.MENOR,
    TipoToken.MAIOR: Op.MAIOR,
    TipoToken.IGUAL_IGUAL: Op.IGUAL,
}

# tokens que podem iniciar um comando
_INICIO_DE_COMANDO = frozenset(
    {TipoToken.PALAVRA_IF, TipoToken.PALAVRA_WHILE, TipoToken.IDENT}
)

# tokens que podem iniciar uma declaracao de topo (var global ou funcao)
_INICIO_DE_DECL = frozenset({TipoToken.PALAVRA_VAR, TipoToken.PALAVRA_FUN})


class ErroSintatico(Exception):
    """Levantada quando a sequencia de tokens nao segue a gramatica Fun."""

    def __init__(self, mensagem: str, posicao: int) -> None:
        self.posicao = posicao
        super().__init__(f"Erro sintatico na posicao {posicao}: {mensagem}")


class AnalisadorSintatico:
    """Constroi a arvore sintatica de uma fonte Fun."""

    def __init__(self, fonte: str) -> None:
        self._lex = AnalisadorLexico(fonte)

    # ----- <programa> ::= <decl>* 'main' '{' <cmd>* 'return' <exp> ';' '}' -----

    def analisa_programa(self) -> Programa:
        declaracoes: list[VarDecl | FunDecl] = []
        tok = self._lex.olhar_proximo()
        while tok.tipo in _INICIO_DE_DECL:
            if tok.tipo == TipoToken.PALAVRA_VAR:
                declaracoes.append(self._analisa_vardecl())
            else:
                declaracoes.append(self._analisa_fundecl())
            tok = self._lex.olhar_proximo()

        self._verifica_token(TipoToken.PALAVRA_MAIN)
        self._verifica_token(TipoToken.CHAVE_ESQ)

        comandos: list[Cmd] = []
        tok = self._lex.olhar_proximo()
        while tok.tipo in _INICIO_DE_COMANDO:
            comandos.append(self._analisa_cmd())
            tok = self._lex.olhar_proximo()

        self._verifica_token(TipoToken.PALAVRA_RETURN)
        exp_final = self._analisa_exp()
        self._verifica_token(TipoToken.PONTO_VIRGULA)
        self._verifica_token(TipoToken.CHAVE_DIR)

        prox = self._lex.proximo_token()
        if prox.tipo != TipoToken.EOF:
            raise ErroSintatico(
                f"esperado fim da entrada, encontrado {self._descreve(prox)}",
                prox.posicao,
            )
        return Programa(tuple(declaracoes), tuple(comandos), exp_final)

    # ----- <vardecl> ::= 'var' <ident> '=' <exp> ';' -----

    def _analisa_vardecl(self) -> VarDecl:
        self._lex.proximo_token()  # consome 'var'
        tok_ident = self._verifica_token(TipoToken.IDENT)
        self._verifica_token(TipoToken.IGUAL)
        exp = self._analisa_exp()
        self._verifica_token(TipoToken.PONTO_VIRGULA)
        return VarDecl(tok_ident.lexema, exp)

    # ----- <fundecl> ::= 'fun' <ident> '(' <arglist>? ')' -----
    #                     '{' <vardecl>* <cmd>* 'return' <exp> ';' '}' -----

    def _analisa_fundecl(self) -> FunDecl:
        self._lex.proximo_token()  # consome 'fun'
        tok_nome = self._verifica_token(TipoToken.IDENT)
        self._verifica_token(TipoToken.PAREN_ESQ)
        params = self._analisa_lista_parametros_formais()
        self._verifica_token(TipoToken.CHAVE_ESQ)

        vardecls: list[VarDecl] = []
        tok = self._lex.olhar_proximo()
        while tok.tipo == TipoToken.PALAVRA_VAR:
            vardecls.append(self._analisa_vardecl())
            tok = self._lex.olhar_proximo()

        comandos: list[Cmd] = []
        while tok.tipo in _INICIO_DE_COMANDO:
            comandos.append(self._analisa_cmd())
            tok = self._lex.olhar_proximo()

        self._verifica_token(TipoToken.PALAVRA_RETURN)
        exp_final = self._analisa_exp()
        self._verifica_token(TipoToken.PONTO_VIRGULA)
        self._verifica_token(TipoToken.CHAVE_DIR)

        return FunDecl(
            tok_nome.lexema, tuple(params), tuple(vardecls), tuple(comandos), exp_final
        )

    def _analisa_lista_parametros_formais(self) -> list[str]:
        """Reconhece <arglist>? logo apos o '(' ja consumido, parando em ')'."""
        params: list[str] = []
        tok = self._lex.olhar_proximo()
        if tok.tipo == TipoToken.PAREN_DIR:
            self._lex.proximo_token()
            return params
        while True:
            tok_ident = self._verifica_token(TipoToken.IDENT)
            params.append(tok_ident.lexema)
            tok = self._lex.olhar_proximo()
            if tok.tipo == TipoToken.VIRGULA:
                self._lex.proximo_token()
                continue
            break
        self._verifica_token(TipoToken.PAREN_DIR)
        return params

    # ----- <cmd> ::= <if> | <while> | <atrib> -----

    def _analisa_cmd(self) -> Cmd:
        tok = self._lex.olhar_proximo()
        if tok.tipo == TipoToken.PALAVRA_IF:
            return self._analisa_if()
        if tok.tipo == TipoToken.PALAVRA_WHILE:
            return self._analisa_while()
        if tok.tipo == TipoToken.IDENT:
            return self._analisa_atrib()
        raise ErroSintatico(
            f"esperado 'if', 'while' ou um identificador (atribuicao), "
            f"encontrado {self._descreve(tok)}",
            tok.posicao,
        )

    def _analisa_bloco_de_comandos(self) -> tuple[Cmd, ...]:
        """Reconhece '{' <cmd>* '}' (usado nos dois blocos do if e no while)."""
        self._verifica_token(TipoToken.CHAVE_ESQ)
        cmds: list[Cmd] = []
        tok = self._lex.olhar_proximo()
        while tok.tipo in _INICIO_DE_COMANDO:
            cmds.append(self._analisa_cmd())
            tok = self._lex.olhar_proximo()
        self._verifica_token(TipoToken.CHAVE_DIR)
        return tuple(cmds)

    # ----- <if> ::= 'if' <exp> '{' <cmd>* '}' 'else' '{' <cmd>* '}' -----

    def _analisa_if(self) -> If:
        self._lex.proximo_token()  # consome 'if'
        cond = self._analisa_exp()
        cmds_then = self._analisa_bloco_de_comandos()
        self._verifica_token(TipoToken.PALAVRA_ELSE)
        cmds_else = self._analisa_bloco_de_comandos()
        return If(cond, cmds_then, cmds_else)

    # ----- <while> ::= 'while' <exp> '{' <cmd>* '}' -----

    def _analisa_while(self) -> While:
        self._lex.proximo_token()  # consome 'while'
        cond = self._analisa_exp()
        cmds = self._analisa_bloco_de_comandos()
        return While(cond, cmds)

    # ----- <atrib> ::= <ident> '=' <exp> ';' -----

    def _analisa_atrib(self) -> Atrib:
        tok_ident = self._lex.proximo_token()  # ja sabemos que e IDENT
        self._verifica_token(TipoToken.IGUAL)
        exp = self._analisa_exp()
        self._verifica_token(TipoToken.PONTO_VIRGULA)
        return Atrib(tok_ident.lexema, exp, tok_ident.posicao)

    # ----- <exp> ::= <exp_a> (('<' | '>' | '==') <exp_a>)* -----

    def _analisa_exp(self) -> Exp:
        esq = self._analisa_exp_a()
        tok = self._lex.olhar_proximo()
        while tok.tipo in _OPERADORES_COMPARACAO:
            self._lex.proximo_token()
            op = _OPERADORES_COMPARACAO[tok.tipo]
            dir_ = self._analisa_exp_a()
            esq = OpBin(op, esq, dir_)
            tok = self._lex.olhar_proximo()
        return esq

    # ----- <exp_a> ::= <exp_m> (('+' | '-') <exp_m>)* -----

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

    # ----- <prim> ::= <num> | <ident> | '(' <exp> ')' | <fun> -----

    def _analisa_prim(self) -> Exp:
        tok = self._lex.proximo_token()
        if tok.tipo == TipoToken.NUMERO:
            return Const(int(tok.lexema))
        if tok.tipo == TipoToken.IDENT:
            # diferencia Var de Chamada olhando o token seguinte: '('
            # indica uma chamada de funcao (secao 4 do enunciado)
            prox = self._lex.olhar_proximo()
            if prox.tipo == TipoToken.PAREN_ESQ:
                return self._analisa_chamada(tok.lexema, tok.posicao)
            return Var(tok.lexema, tok.posicao)
        if tok.tipo == TipoToken.PAREN_ESQ:
            interna = self._analisa_exp()
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

    # ----- <fun> ::= <ident> '(' <params>? ')' -----

    def _analisa_chamada(self, nome: str, posicao: int) -> Chamada:
        self._verifica_token(TipoToken.PAREN_ESQ)
        args = self._analisa_lista_parametros_reais()
        return Chamada(nome, tuple(args), posicao)

    def _analisa_lista_parametros_reais(self) -> list[Exp]:
        """Reconhece <params>? logo apos o '(' ja consumido, parando em ')'."""
        args: list[Exp] = []
        tok = self._lex.olhar_proximo()
        if tok.tipo == TipoToken.PAREN_DIR:
            self._lex.proximo_token()
            return args
        while True:
            args.append(self._analisa_exp())
            tok = self._lex.olhar_proximo()
            if tok.tipo == TipoToken.VIRGULA:
                self._lex.proximo_token()
                continue
            break
        self._verifica_token(TipoToken.PAREN_DIR)
        return args

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
